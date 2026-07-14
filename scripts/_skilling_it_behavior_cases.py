"""Strict case-schema and fixture filesystem helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CASE_FIELDS = {
    "case_id",
    "prompt",
    "replies",
    "reply_updates",
    "initial_files",
    "initial_file_modes",
    "mutation",
    "criteria",
    "destination_selected",
    "synthetic_deployment_allowed",
    "synthetic_targets",
    "synthetic_target_updates",
    "synthetic_execution_allowed",
    "synthetic_command",
}


def contained_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes declared root: {relative}")
    return candidate


def _file_map(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or not all(
        isinstance(path, str) and isinstance(content, str)
        for path, content in value.items()
    ):
        raise ValueError(f"{label} must be a string file mapping")
    for relative in value:
        contained_path(Path("/synthetic-root"), relative)
    return value


def validate_case(case: Any) -> None:
    if not isinstance(case, dict):
        raise ValueError("behavior case must be an object")
    unknown = set(case) - CASE_FIELDS
    if unknown:
        raise ValueError(f"behavior case has undeclared fields: {sorted(unknown)}")
    required = {"case_id", "prompt", "replies", "initial_files", "mutation", "criteria"}
    missing = required - set(case)
    if missing:
        raise ValueError(f"case missing fields {sorted(missing)}: {case}")
    if not isinstance(case["prompt"], str) or not isinstance(case["replies"], list):
        raise ValueError("prompt must be a string and replies must be a list")
    if not all(isinstance(reply, str) for reply in case["replies"]):
        raise ValueError("replies must contain strings")
    _file_map(case["initial_files"], "initial_files")
    if case["mutation"] not in {"none", "allowed", "required"}:
        raise ValueError("mutation must be none, allowed, or required")
    if (
        not isinstance(case["criteria"], list)
        or not case["criteria"]
        or not all(isinstance(item, str) and item.strip() for item in case["criteria"])
    ):
        raise ValueError("criteria must be a non-empty string list")
    if not isinstance(case.get("destination_selected", True), bool):
        raise ValueError("destination_selected must be boolean")

    updates = case.get("reply_updates", [])
    if not isinstance(updates, list) or len(updates) > len(case["replies"]):
        raise ValueError("reply_updates must align with replies")
    for update in updates:
        _file_map(update, "reply_updates")
    modes = case.get("initial_file_modes", {})
    if not isinstance(modes, dict) or not set(modes) <= set(case["initial_files"]):
        raise ValueError("initial_file_modes must name initial_files only")
    if not all(
        isinstance(mode, str) and re.fullmatch(r"0?[0-7]{3}", mode)
        for mode in modes.values()
    ):
        raise ValueError("initial_file_modes must contain octal strings")

    deploy = case.get("synthetic_deployment_allowed", False)
    targets = case.get("synthetic_targets", {})
    target_updates = case.get("synthetic_target_updates", [])
    if not isinstance(deploy, bool) or not isinstance(targets, dict):
        raise ValueError("synthetic deployment fields have invalid shapes")
    if bool(targets) != deploy or (target_updates and not deploy):
        raise ValueError("synthetic targets require explicit deployment allowance")
    for name, target in targets.items():
        if not isinstance(name, str) or not CASE_ID_PATTERN.fullmatch(name):
            raise ValueError(f"invalid synthetic target name: {name!r}")
        if not isinstance(target, dict) or set(target) != {"initial_files", "readback"}:
            raise ValueError(f"invalid synthetic target shape: {name}")
        _file_map(target["initial_files"], f"synthetic target {name}")
        if target["readback"] not in {"available", "unavailable"}:
            raise ValueError(f"invalid readback state for {name}")
    if not isinstance(target_updates, list) or len(target_updates) > len(
        case["replies"]
    ):
        raise ValueError("synthetic_target_updates must align with replies")
    for update in target_updates:
        if not isinstance(update, dict) or not set(update) <= set(targets):
            raise ValueError("synthetic target update names an undeclared target")
        for state in update.values():
            if (
                not isinstance(state, dict)
                or set(state) != {"readback"}
                or state["readback"] not in {"available", "unavailable"}
            ):
                raise ValueError("synthetic target update has invalid state")

    execute = case.get("synthetic_execution_allowed", False)
    command = case.get("synthetic_command", [])
    if not isinstance(execute, bool) or bool(command) != execute:
        raise ValueError("synthetic command requires explicit execution allowance")
    if command:
        if (
            not isinstance(command, list)
            or len(command) < 2
            or command[0] != "python3"
            or not all(
                isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9_./-]+", token)
                for token in command
            )
        ):
            raise ValueError("synthetic_command must be a safe python3 argv list")
        script = command[1]
        if (
            script.startswith("-")
            or not script.endswith(".py")
            or script not in case["initial_files"]
        ):
            raise ValueError("synthetic_command must name a staged Python script")
        for token in command[1:]:
            if not token.startswith("-"):
                contained_path(Path("/synthetic-root"), token)


def reject_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise ValueError(f"symlink is not allowed in staged source: {root}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed in staged source: {path}")


def seed_files(
    root: Path, files: dict[str, str], modes: dict[str, str] | None = None
) -> None:
    modes = modes or {}
    for relative, content in files.items():
        path = contained_path(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_text(content, encoding="utf-8")
        path.chmod(int(modes[relative], 8) if relative in modes else 0o600)


def load_execution_expectations(
    path: Path, cases: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    expectations = json.loads(path.read_text(encoding="utf-8"))
    command_cases = {
        case["case_id"] for case in cases if case.get("synthetic_execution_allowed")
    }
    if not isinstance(expectations, dict) or set(expectations) != command_cases:
        raise ValueError("execution expectations must exactly cover synthetic commands")
    allowed = {"exit_code", "error_code", "corrective_action", "path_suffix"}
    for case_id, expectation in expectations.items():
        if (
            not isinstance(expectation, dict)
            or set(expectation) - allowed
            or not {"exit_code", "error_code", "corrective_action"} <= set(expectation)
            or not isinstance(expectation["exit_code"], int)
            or expectation["exit_code"] == 0
            or not all(
                isinstance(expectation[key], str) and expectation[key]
                for key in set(expectation) - {"exit_code"}
            )
        ):
            raise ValueError(f"invalid execution expectation: {case_id}")
    return expectations


def execution_receipt_matches(
    receipt: dict[str, Any], argv: list[str], expectation: dict[str, Any]
) -> bool:
    if not argv:
        return not receipt and not expectation
    try:
        payload = json.loads(receipt.get("stderr", ""))
    except (json.JSONDecodeError, TypeError):
        return False
    error = payload.get("error") if isinstance(payload, dict) else None
    return bool(
        receipt.get("argv") == argv
        and receipt.get("exit_code") == expectation.get("exit_code")
        and isinstance(error, dict)
        and error.get("code") == expectation.get("error_code")
        and error.get("corrective_action") == expectation.get("corrective_action")
        and (
            "path_suffix" not in expectation
            or (
                isinstance(error.get("path"), str)
                and error["path"].endswith(expectation["path_suffix"])
            )
        )
    )
