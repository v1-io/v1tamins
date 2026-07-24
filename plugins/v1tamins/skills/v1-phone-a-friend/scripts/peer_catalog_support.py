"""Provider discovery primitives for :mod:`peer_catalog`.

This module owns provider-specific probing and catalog parsing. The sibling
``peer_catalog.py`` module owns profile selection, freshness checks, and the
JSON command-line contract.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Iterable


SCHEMA = "v1-peer-catalog/v1"
DEFAULT_TIMEOUT_SECONDS = 8
KNOWN_EFFORT_ORDER = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)
KNOWN_EFFORT_RANK = {name: index for index, name in enumerate(KNOWN_EFFORT_ORDER)}

# These are names only. Values are never printed, hashed, or passed through in
# subscription_native mode. Provider-native OAuth variables remain available.
API_KEY_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_AUTH_TOKEN",
    "CODEX_API_KEY",
    "CURSOR_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_API_KEY",
)

PROVIDER_KEY_ENV_VARS = {
    "claude": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_API_KEY"),
    "codex": ("OPENAI_API_KEY", "OPENAI_AUTH_TOKEN", "CODEX_API_KEY"),
    "cursor-agent": ("CURSOR_API_KEY",),
    "agy": ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"),
}


@dataclass(frozen=True)
class ProviderSpec:
    binary: str
    catalog_args: tuple[str, ...] | None
    auth_args: tuple[str, ...] | None
    subscription_supported: bool
    roles: tuple[str, ...]


PROVIDERS: dict[str, ProviderSpec] = {
    "claude": ProviderSpec(
        "claude",
        None,
        ("doctor",),
        True,
        ("correctness/security", "structural review", "maintainability"),
    ),
    "codex": ProviderSpec(
        "codex",
        None,
        ("doctor", "--json"),
        True,
        ("structural review", "correctness/security", "verification"),
    ),
    "cursor-agent": ProviderSpec(
        "cursor-agent",
        ("--list-models",),
        ("status",),
        True,
        ("structural review", "maintainability", "verification"),
    ),
    "agy": ProviderSpec(
        "agy",
        ("models",),
        None,
        True,
        ("large-context", "multimodal", "research"),
    ),
    "gemini": ProviderSpec(
        "gemini",
        None,
        None,
        False,
        ("large-context", "research"),
    ),
}


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def bounded_text(value: str, limit: int = 400) -> str:
    """Keep diagnostics deterministic and prevent accidental large echoes."""

    return re.sub(r"\s+", " ", value.strip())[:limit]


def subscription_environment(mode: str) -> dict[str, str]:
    if mode not in {"subscription_native", "api_explicit"}:
        raise ValueError(f"unsupported auth mode: {mode}")

    environment = dict(os.environ)
    if mode == "subscription_native":
        for name in API_KEY_ENV_VARS:
            environment.pop(name, None)
    return environment


def run_command(
    command: list[str], mode: str, timeout_seconds: float
) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            errors="replace",
            env=subscription_environment(mode),
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return CommandResult(None, stdout, stderr, timed_out=True)
    except OSError as exc:
        return CommandResult(127, "", str(exc))

    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def parse_json_models(value: Any) -> list[Any]:
    if isinstance(value, dict):
        for key in ("models", "data", "items", "available_models"):
            if key in value:
                return parse_json_models(value[key])
        return [value]
    if isinstance(value, list):
        return value
    return []


def effort_name(value: str) -> str | None:
    normalized = value.strip().lower().replace("-", "")
    aliases = {
        "none": "none",
        "minimal": "minimal",
        "low": "low",
        "medium": "medium",
        "med": "medium",
        "high": "high",
        "xhigh": "xhigh",
        "extra high": "xhigh",
        "max": "max",
    }
    return aliases.get(normalized)


def efforts_from_text(text: str) -> list[str]:
    found: set[str] = set()
    for token in re.findall(
        r"(?i)(?<![A-Za-z])(?:none|minimal|low|medium|med|high|x[- ]?high|max)(?![A-Za-z])",
        text,
    ):
        normalized = effort_name(token)
        if normalized:
            found.add(normalized)
    return sorted(found, key=lambda item: KNOWN_EFFORT_RANK[item])


def model_family(model_id: str) -> str:
    """Derive a coarse family without knowing provider model names."""

    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", model_id).strip("-").lower()
    if not cleaned:
        return "unknown"
    return cleaned.split("-")[0]


def effort_suffix(model_id: str) -> str | None:
    tokens = re.split(r"[-_:]", model_id.lower())
    for token in reversed(tokens):
        normalized = effort_name(token)
        if normalized:
            return normalized
    return None


def normalize_model_entry(
    value: Any, rank: int, advertised_efforts: Iterable[str]
) -> dict[str, Any] | None:
    if isinstance(value, str):
        model_id = value.strip()
        metadata: dict[str, Any] = {}
    elif isinstance(value, dict):
        raw_id = value.get("id") or value.get("name") or value.get("model")
        model_id = str(raw_id).strip() if raw_id is not None else ""
        metadata = value
    else:
        return None

    if not model_id or len(model_id) > 200 or re.match(r"^[-<]", model_id):
        return None
    if model_id.lower() in {"model", "models", "available", "available-models"}:
        return None

    explicit_efforts = metadata.get("efforts") or metadata.get("reasoning_levels")
    if isinstance(explicit_efforts, str):
        explicit_efforts = [explicit_efforts]
    if isinstance(explicit_efforts, list):
        efforts = [effort_name(str(item)) for item in explicit_efforts]
        efforts = [item for item in efforts if item]
    else:
        suffix = effort_suffix(model_id)
        efforts = [suffix] if suffix else list(advertised_efforts)

    return {
        "id": model_id,
        "family": str(metadata.get("family") or model_family(model_id)),
        "efforts": sorted(set(efforts), key=lambda item: KNOWN_EFFORT_RANK[item]),
        "rank": rank,
    }


def parse_model_catalog(
    text: str, advertised_efforts: Iterable[str] = ()
) -> list[dict[str, Any]]:
    """Parse provider JSON or line-oriented picker output.

    Provider-native JSON is preferred. Text parsing is intentionally limited to
    one token per non-heading line and is marked degraded by the caller.
    """

    values: list[Any] = []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
    if payload is not None:
        values = parse_json_models(payload)
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.endswith(":"):
                continue
            if re.match(r"(?i)^(available|models?|tips?|usage|options?)\b", line):
                continue
            parts = line.split()
            token = parts[0].strip("`'\"(),")
            if token.startswith("-") or token.startswith("<"):
                continue
            if len(parts) > 1 and not re.search(r"[-_.:/=+@0-9]", token):
                continue
            if re.match(r"^[A-Za-z0-9][A-Za-z0-9_.:/=+@-]*$", token):
                values.append(token)

    models: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rank, value in enumerate(values):
        model = normalize_model_entry(value, rank, advertised_efforts)
        if model is None or model["id"] in seen:
            continue
        seen.add(model["id"])
        models.append(model)
    return models


def help_model_aliases(text: str, advertised_efforts: Iterable[str]) -> list[dict[str, Any]]:
    """Extract aliases only when the current help text explicitly advertises them."""

    values: list[str] = []
    for match in re.finditer(
        r"(?i)(?:e\.g\.|for example|such as)([^\n.)]{0,160})", text
    ):
        values.extend(
            re.findall(
                r"(?<![A-Za-z])([A-Za-z][A-Za-z0-9_.:-]{1,48})(?![A-Za-z])",
                match.group(1),
            )
        )

    # Avoid treating prose words as models. The surrounding option text is
    # still useful for effort discovery, but only model-looking aliases that
    # occur next to a model option are accepted.
    model_section = " ".join(
        line for line in text.splitlines() if "--model" in line or "model" in line.lower()
    )
    allowed = set(
        re.findall(
            r"(?<![A-Za-z])([A-Za-z][A-Za-z0-9_.:-]{1,48})(?![A-Za-z])",
            model_section,
        )
    )
    filtered = [value for value in values if value in allowed]
    return parse_model_catalog("\n".join(filtered), advertised_efforts)


def parse_structured_auth(text: str) -> bool | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    def visit(value: Any) -> bool | None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in {"authenticated", "logged_in", "loggedin", "authorized"} and isinstance(child, bool):
                    return child
                result = visit(child)
                if result is not None:
                    return result
        elif isinstance(value, list):
            for child in value:
                result = visit(child)
                if result is not None:
                    return result
        return None

    return visit(payload)


def auth_result(
    name: str, spec: ProviderSpec, mode: str, auth_probe: CommandResult | None
) -> dict[str, Any]:
    key_names = [name for name in PROVIDER_KEY_ENV_VARS.get(name, ()) if os.environ.get(name)]
    if mode == "subscription_native" and key_names:
        return {
            "source": "unverified",
            "confidence": "degraded",
            "credential_presence": "api_key_present",
            "policy_state": "blocked_api_key_present",
            "key_env_names": key_names,
        }

    if mode == "api_explicit":
        if key_names:
            return {
                "source": "api_explicit",
                "confidence": "unresolved",
                "credential_presence": "api_key_present",
                "policy_state": "explicit_api_mode",
                "key_env_names": key_names,
            }
        return {
            "source": "unavailable",
            "confidence": "unresolved",
            "credential_presence": "none_detected",
            "policy_state": "api_key_required",
            "key_env_names": [],
        }

    if not spec.subscription_supported:
        return {
            "source": "unavailable",
            "confidence": "verified",
            "credential_presence": "not_applicable",
            "policy_state": "subscription_workflow_unsupported",
            "key_env_names": [],
        }

    if auth_probe is not None and not auth_probe.timed_out:
        structured = parse_structured_auth(auth_probe.stdout)
        if structured is True:
            return {
                "source": "subscription_native",
                "confidence": "verified",
                "credential_presence": "none_detected",
                "policy_state": "eligible",
                "key_env_names": [],
            }
        if structured is False:
            return {
                "source": "unavailable",
                "confidence": "verified",
                "credential_presence": "none_detected",
                "policy_state": "not_authenticated",
                "key_env_names": [],
            }

        status_text = f"{auth_probe.stdout}\n{auth_probe.stderr}"
        if re.search(r"(?i)\bnot\s+(?:logged\s+in|authenticated|authorized)\b", status_text):
            return {
                "source": "unavailable",
                "confidence": "degraded",
                "credential_presence": "none_detected",
                "policy_state": "not_authenticated",
                "key_env_names": [],
            }
        if re.search(r"(?i)\b(?:logged\s+in|authenticated|authorized)\b", status_text):
            return {
                "source": "subscription_native",
                "confidence": "degraded",
                "credential_presence": "none_detected",
                "policy_state": "eligible",
                "key_env_names": [],
            }

    return {
        "source": "unverified",
        "confidence": "unresolved",
        "credential_presence": "none_detected",
        "policy_state": "auth_not_verified",
        "key_env_names": [],
    }


def advertised_efforts_from_help(text: str) -> list[str]:
    return efforts_from_text(text)


def first_version_line(result: CommandResult) -> str | None:
    for line in result.stdout.splitlines():
        clean = bounded_text(line, 200)
        if clean:
            return clean
    return None


def discover_provider(
    name: str, mode: str, timeout_seconds: float
) -> dict[str, Any]:
    spec = PROVIDERS[name]
    executable = shutil.which(spec.binary)
    base: dict[str, Any] = {
        "cli": name,
        "installed": executable is not None,
        "executable": executable,
        "version": None,
        "version_fingerprint": None,
        "auth": None,
        "models": [],
        "model_catalog": {
            "status": "unresolved",
            "confidence": "unresolved",
            "source": None,
            "fingerprint": None,
        },
        "reasoning_levels": [],
        "roles": list(spec.roles),
        "workflow": "available" if spec.subscription_supported else "subscription_unsupported",
    }
    if executable is None:
        base["auth"] = {
            "source": "unavailable",
            "confidence": "verified",
            "credential_presence": "not_checked",
            "policy_state": "not_installed",
            "key_env_names": [],
        }
        return base

    version_result = run_command([executable, "--version"], mode, timeout_seconds)
    base["version"] = first_version_line(version_result)
    base["version_fingerprint"] = sha256_text(
        f"{name}\n{base['version'] or ''}\n{version_result.returncode}"
    )

    help_result = run_command([executable, "--help"], mode, timeout_seconds)
    help_text = help_result.stdout
    efforts = advertised_efforts_from_help(help_text)
    base["reasoning_levels"] = efforts

    auth_probe = None
    if spec.auth_args is not None:
        auth_probe = run_command([executable, *spec.auth_args], mode, timeout_seconds)
    base["auth"] = auth_result(name, spec, mode, auth_probe)

    catalog_result: CommandResult | None = None
    catalog_source = None
    catalog_confidence = "unresolved"
    if spec.catalog_args is not None:
        catalog_result = run_command([executable, *spec.catalog_args], mode, timeout_seconds)
        if catalog_result.returncode == 0 and not catalog_result.timed_out:
            catalog_source = "provider_catalog"
            catalog_confidence = "verified"
    elif help_text and spec.subscription_supported:
        aliases = help_model_aliases(help_text, efforts)
        if aliases:
            base["models"] = aliases
            catalog_source = "documented_help_examples"
            catalog_confidence = "degraded"

    if catalog_result is not None and catalog_source == "provider_catalog":
        base["models"] = parse_model_catalog(
            catalog_result.stdout, advertised_efforts=efforts
        )
        if not base["models"]:
            catalog_source = None
            catalog_confidence = "unresolved"

    raw_catalog = ""
    if catalog_result is not None:
        raw_catalog = catalog_result.stdout
    elif help_text and base["models"]:
        raw_catalog = "\n".join(model["id"] for model in base["models"])
    if raw_catalog:
        base["model_catalog"] = {
            "status": "resolved",
            "confidence": catalog_confidence,
            "source": catalog_source,
            "fingerprint": sha256_text(raw_catalog),
        }
    base["models"] = [
        {
            **model,
            "reasoning_levels": model["efforts"] or efforts,
        }
        for model in base["models"]
    ]
    return base
