"""Structured provider discovery for peer catalog selection."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from peer_models import AuthFact, ModelCatalog, ModelEntry, ProviderDiscovery
from peer_policy import PROVIDER_KEY_ENV_VARS, PROVIDERS, ProviderSpec, subscription_environment

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


def run_command(command: list[str], mode: str, timeout_seconds: float) -> CommandResult:
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
        "extrahigh": "xhigh",
        "max": "max",
    }
    return aliases.get(normalized)


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
    value: Any, rank: int, advertised_efforts: Iterable[str] = ()
) -> ModelEntry | None:
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
        efforts_list = [item for item in efforts if item]
    else:
        suffix = effort_suffix(model_id)
        efforts_list = [suffix] if suffix else [item for item in advertised_efforts]

    ordered = tuple(sorted(set(efforts_list), key=lambda item: KNOWN_EFFORT_RANK[item]))
    return ModelEntry(
        id=model_id,
        family=str(metadata.get("family") or model_family(model_id)),
        efforts=ordered,
        reasoning_levels=ordered,
        rank=rank,
    )


def parse_model_catalog(
    text: str, advertised_efforts: Iterable[str] = ()
) -> list[ModelEntry]:
    """Parse provider catalog command output only.

    JSON is preferred. Line-oriented parsing covers dedicated list commands such
    as ``agy models`` and cursor-agent ``--list-models`` lines shaped like
    ``id - label``. Help text and prose are not catalog sources.
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
            # cursor-agent: "id - label"; agy: one id per line.
            if " - " in line:
                token = line.split(" - ", 1)[0].strip()
            else:
                parts = line.split()
                token = parts[0].strip("`'\"(),") if parts else ""
                # Reject prose lines that are not model-shaped identifiers.
                if len(parts) > 1 and not re.search(r"[-_.:/=+@0-9]", token):
                    continue
            if not token or token.startswith("-") or token.startswith("<"):
                continue
            if re.match(r"^[A-Za-z0-9][A-Za-z0-9_.:/=+@-]*$", token):
                values.append(token)

    models: list[ModelEntry] = []
    seen: set[str] = set()
    for rank, value in enumerate(values):
        model = normalize_model_entry(value, rank, advertised_efforts)
        if model is None or model.id in seen:
            continue
        seen.add(model.id)
        models.append(model)
    return models


def ambient_provider_keys(name: str) -> list[str]:
    return [key for key in PROVIDER_KEY_ENV_VARS.get(name, ()) if os.environ.get(key)]


def policy_auth(name: str, mode: str) -> AuthFact | None:
    """Apply credential policy before provider-specific auth probes."""

    key_names = ambient_provider_keys(name)
    if mode == "subscription_native" and key_names:
        return AuthFact(
            source="unverified",
            confidence="degraded",
            credential_presence="api_key_present",
            policy_state="blocked_api_key_present",
            key_env_names=tuple(key_names),
        )
    if mode == "api_explicit":
        if key_names:
            return AuthFact(
                source="api_explicit",
                confidence="unresolved",
                credential_presence="api_key_present",
                policy_state="explicit_api_mode",
                key_env_names=tuple(key_names),
            )
        return AuthFact(
            source="unavailable",
            confidence="unresolved",
            credential_presence="none_detected",
            policy_state="api_key_required",
            key_env_names=(),
        )
    return None


def parse_codex_doctor_auth(payload: Any) -> bool | None:
    """Recognize only the structured codex doctor credentials shape."""

    def visit(value: Any) -> bool | None:
        if isinstance(value, dict):
            status = str(value.get("status", "")).strip().lower()
            details = value.get("details")
            if status in {"ok", "pass", "passed"} and isinstance(details, dict):
                normalized = {
                    str(key).strip().lower(): str(child).strip().lower()
                    for key, child in details.items()
                }
                stored_tokens = normalized.get("stored chatgpt tokens")
                auth_mode = normalized.get("stored auth mode")
                if stored_tokens in {"true", "yes"} or auth_mode in {
                    "chatgpt",
                    "oauth",
                    "subscription",
                    "subscription_native",
                }:
                    return True
            for child in value.values():
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


def auth_from_claude(probe: CommandResult) -> AuthFact | None:
    if probe.timed_out or not probe.stdout.strip():
        return None
    try:
        payload = json.loads(probe.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "loggedIn" not in payload:
        return None
    logged_in = payload.get("loggedIn")
    if logged_in is True:
        return AuthFact(
            source="subscription_native",
            confidence="verified",
            credential_presence="none_detected",
            policy_state="eligible",
        )
    if logged_in is False:
        return AuthFact(
            source="unavailable",
            confidence="verified",
            credential_presence="none_detected",
            policy_state="not_authenticated",
        )
    return None


def auth_from_codex(probe: CommandResult) -> AuthFact | None:
    if probe.timed_out or not probe.stdout.strip():
        return None
    try:
        payload = json.loads(probe.stdout)
    except json.JSONDecodeError:
        return None
    structured = parse_codex_doctor_auth(payload)
    if structured is True:
        return AuthFact(
            source="subscription_native",
            confidence="verified",
            credential_presence="none_detected",
            policy_state="eligible",
        )
    if structured is False:
        return AuthFact(
            source="unavailable",
            confidence="verified",
            credential_presence="none_detected",
            policy_state="not_authenticated",
        )
    return None


def auth_from_cursor(probe: CommandResult) -> AuthFact | None:
    if probe.timed_out or not probe.stdout.strip():
        return None
    try:
        payload = json.loads(probe.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if "isAuthenticated" in payload:
        if payload.get("isAuthenticated") is True:
            return AuthFact(
                source="subscription_native",
                confidence="verified",
                credential_presence="none_detected",
                policy_state="eligible",
            )
        if payload.get("isAuthenticated") is False:
            return AuthFact(
                source="unavailable",
                confidence="verified",
                credential_presence="none_detected",
                policy_state="not_authenticated",
            )
    status = str(payload.get("status", "")).strip().lower()
    if status in {"authenticated", "authorized", "ok"}:
        return AuthFact(
            source="subscription_native",
            confidence="verified",
            credential_presence="none_detected",
            policy_state="eligible",
        )
    if status in {"unauthenticated", "unauthorized", "logged_out"}:
        return AuthFact(
            source="unavailable",
            confidence="verified",
            credential_presence="none_detected",
            policy_state="not_authenticated",
        )
    return None


def auth_result(
    name: str, spec: ProviderSpec, mode: str, auth_probe: CommandResult | None
) -> AuthFact:
    del spec  # reserved for provider-specific extensions
    policy = policy_auth(name, mode)
    if policy is not None:
        return policy

    if mode == "api_explicit":
        # policy_auth always returns for api_explicit
        return AuthFact(
            source="unavailable",
            confidence="unresolved",
            credential_presence="none_detected",
            policy_state="api_key_required",
        )

    if name == "agy":
        return AuthFact(
            source="unverified",
            confidence="unresolved",
            credential_presence="none_detected",
            policy_state="auth_not_verified",
        )

    if auth_probe is None:
        return AuthFact(
            source="unverified",
            confidence="unresolved",
            credential_presence="none_detected",
            policy_state="auth_not_verified",
        )

    parsed: AuthFact | None = None
    if name == "claude":
        parsed = auth_from_claude(auth_probe)
    elif name == "codex":
        parsed = auth_from_codex(auth_probe)
    elif name == "cursor-agent":
        parsed = auth_from_cursor(auth_probe)

    if parsed is not None:
        return parsed

    return AuthFact(
        source="unverified",
        confidence="unresolved",
        credential_presence="none_detected",
        policy_state="auth_not_verified",
    )


def first_version_line(result: CommandResult) -> str | None:
    for line in result.stdout.splitlines():
        clean = bounded_text(line, 200)
        if clean:
            return clean
    return None


def discover_provider(
    name: str, mode: str, timeout_seconds: float
) -> ProviderDiscovery:
    spec = PROVIDERS[name]
    executable = shutil.which(spec.binary)
    unresolved_catalog = ModelCatalog(
        status="unresolved",
        confidence="unresolved",
        source=None,
        fingerprint=None,
    )
    if executable is None:
        return ProviderDiscovery(
            cli=name,
            installed=False,
            executable=None,
            version=None,
            version_fingerprint=None,
            auth=AuthFact(
                source="unavailable",
                confidence="verified",
                credential_presence="not_checked",
                policy_state="not_installed",
            ),
            models=(),
            model_catalog=unresolved_catalog,
            reasoning_levels=(),
            roles=spec.roles,
            workflow="available",
        )

    version_result = run_command([executable, "--version"], mode, timeout_seconds)
    version = first_version_line(version_result)
    version_fingerprint = sha256_text(f"{name}\n{version or ''}\n{version_result.returncode}")

    auth_probe = None
    if spec.auth_args is not None:
        auth_probe = run_command([executable, *spec.auth_args], mode, timeout_seconds)
    auth = auth_result(name, spec, mode, auth_probe)

    models: list[ModelEntry] = []
    catalog = unresolved_catalog
    if spec.catalog_args is not None:
        catalog_result = run_command(
            [executable, *spec.catalog_args], mode, timeout_seconds
        )
        if catalog_result.returncode == 0 and not catalog_result.timed_out:
            models = parse_model_catalog(catalog_result.stdout)
            if models:
                catalog = ModelCatalog(
                    status="resolved",
                    confidence="verified",
                    source="provider_catalog",
                    fingerprint=sha256_text(catalog_result.stdout),
                )

    reasoning_levels = tuple(
        sorted(
            {level for model in models for level in model.reasoning_levels},
            key=lambda item: KNOWN_EFFORT_RANK[item],
        )
    )
    enriched = tuple(
        ModelEntry(
            id=model.id,
            family=model.family,
            efforts=model.efforts,
            reasoning_levels=model.reasoning_levels or reasoning_levels,
            rank=model.rank,
        )
        for model in models
    )
    return ProviderDiscovery(
        cli=name,
        installed=True,
        executable=executable,
        version=version,
        version_fingerprint=version_fingerprint,
        auth=auth,
        models=enriched,
        model_catalog=catalog,
        reasoning_levels=reasoning_levels,
        roles=spec.roles,
        workflow="available",
    )
