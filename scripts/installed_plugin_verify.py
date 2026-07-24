#!/usr/bin/env python3
"""Read-only comparison of a canonical plugin root with one installed root."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "v1-installed-plugin-verification/v1"

REQUIRED_RELPATHS = (
    "skills/v1-phone-a-friend/SKILL.md",
    "skills/v1-review-board/SKILL.md",
    "skills/v1-phone-a-friend/scripts/peer_catalog.py",
    "skills/v1-phone-a-friend/scripts/peer_policy.py",
    "skills/v1-phone-a-friend/scripts/peer_adapters.py",
    "skills/v1-phone-a-friend/scripts/peer_models.py",
)

REQUIRED_EXECUTABLE_RELPATHS = (
    "skills/v1-phone-a-friend/scripts/peer-run.sh",
    "skills/v1-phone-a-friend/scripts/peer-env.sh",
    "skills/v1-phone-a-friend/scripts/peer-run-inner.sh",
    "skills/v1-phone-a-friend/scripts/peer-run-watchdog.sh",
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True))


def status_payload(
    runtime: str, status: str, message: str | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "runtime": runtime,
        "verification_status": status,
        "action_status": "not_requested",
        "credential_values_exposed": False,
    }
    if message is not None:
        payload["message"] = message
    return payload


def _is_private_or_generated(relative: Path) -> bool:
    parts = relative.parts
    if any(part == "__pycache__" or part.startswith("v1-_") for part in parts):
        return True
    if relative.suffix in {".pyc", ".pyo"}:
        return True
    return False


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for current, directories, files in os.walk(root, followlinks=False):
        # Skip private plugin skills and bytecode directories in-place.
        directories[:] = [
            name
            for name in sorted(directories)
            if name != "__pycache__" and not name.startswith("v1-_")
        ]
        for name in sorted(files):
            path = Path(current) / name
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if _is_private_or_generated(relative):
                continue
            digest.update(relative.as_posix().encode())
            digest.update(b"\0")
            mode = path.stat().st_mode & 0o777
            digest.update(f"{mode:03o}".encode())
            digest.update(b"\0")
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
    return digest.hexdigest()


def required_helpers_executable(root: Path) -> bool:
    for relpath in REQUIRED_EXECUTABLE_RELPATHS:
        path = root / relpath
        if not path.is_file():
            return False
        mode = path.stat().st_mode
        if not (mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)):
            return False
    return True


def manifest_version(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = payload.get("version")
    return value if isinstance(value, str) and value.strip() else None


def probe_catalog(script: Path) -> tuple[str, str | None]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(script),
                "--profile",
                "fast",
                "--auth-mode",
                "subscription_native",
            ],
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=60,
            env=env,
            cwd=str(script.parent),
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable", None
    if completed.returncode != 0:
        return "unavailable", None
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return "invalid", None
    fingerprint = payload.get("catalog_fingerprint")
    if not (isinstance(fingerprint, str) and fingerprint):
        return "invalid", None
    discovered = payload.get("discovered")
    if not isinstance(discovered, list):
        return "unresolved", fingerprint
    if any(
        isinstance(item, dict)
        and isinstance(item.get("model_catalog"), dict)
        and item["model_catalog"].get("status") == "resolved"
        for item in discovered
    ):
        return "resolved", fingerprint
    return "unresolved", fingerprint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--installed", action="append", default=[])
    parser.add_argument("--runtime", required=True, choices=("codex", "claude"))
    parser.add_argument(
        "--probe-catalog",
        action="store_true",
        help="run installed peer_catalog once; default leaves catalog not_requested",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime = args.runtime
    manifest_relpath = (
        ".codex-plugin/plugin.json"
        if runtime == "codex"
        else ".claude-plugin/plugin.json"
    )

    if not args.installed:
        emit(status_payload(runtime, "missing", "no installed root supplied"))
        return 1
    if len(args.installed) != 1:
        emit(
            status_payload(
                runtime, "ambiguous", "more than one installed root supplied"
            )
        )
        return 1

    canonical = Path(args.canonical)
    installed = Path(args.installed[0])
    if not canonical.is_dir() or not (canonical / manifest_relpath).is_file():
        emit(
            status_payload(
                runtime,
                "missing",
                "canonical plugin root is missing the selected runtime manifest",
            )
        )
        return 1
    if not installed.is_dir() or not (installed / manifest_relpath).is_file():
        emit(
            status_payload(
                runtime,
                "missing",
                "installed plugin root is missing the selected runtime manifest",
            )
        )
        return 1

    for relpath in REQUIRED_RELPATHS:
        if not (canonical / relpath).is_file() or not (installed / relpath).is_file():
            emit(
                status_payload(
                    runtime, "missing", "required peer skill resource is missing"
                )
            )
            return 1

    if not required_helpers_executable(canonical) or not required_helpers_executable(
        installed
    ):
        emit(
            status_payload(
                runtime,
                "missing",
                "required peer helper scripts are missing execute permission",
            )
        )
        return 1

    canonical_version = manifest_version(canonical / manifest_relpath)
    installed_version = manifest_version(installed / manifest_relpath)
    if canonical_version is None or installed_version is None:
        emit(status_payload(runtime, "missing", "runtime manifest is not valid JSON"))
        return 1

    canonical_source = tree_hash(canonical.resolve())
    installed_source = tree_hash(installed.resolve())

    catalog_status = "not_requested"
    catalog_fingerprint: str | None = None
    if args.probe_catalog:
        catalog_status, catalog_fingerprint = probe_catalog(
            installed / "skills/v1-phone-a-friend/scripts/peer_catalog.py"
        )

    verification_status = "match"
    if canonical_version != installed_version or canonical_source != installed_source:
        verification_status = "stale"

    emit(
        {
            "schema": SCHEMA,
            "runtime": runtime,
            "verification_status": verification_status,
            "action_status": "not_requested",
            "canonical_version": canonical_version,
            "installed_version": installed_version,
            "canonical_source_sha256": canonical_source,
            "installed_source_sha256": installed_source,
            "model_catalog_status": catalog_status,
            "model_catalog_fingerprint": catalog_fingerprint,
            "credential_values_exposed": False,
        }
    )
    return 0 if verification_status == "match" else 1


if __name__ == "__main__":
    raise SystemExit(main())
