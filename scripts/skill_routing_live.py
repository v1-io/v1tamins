#!/usr/bin/env python3
"""Shared helpers for opt-in live v1tamins skill routing evals."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RESULT_SCHEMA_VERSION = "v1"
ADAPTER_VERSION = "v1"
EVIDENCE_KINDS = {"observed_invocation", "structured_decision", "inconclusive"}
RUNTIMES = {"codex", "claude"}
STATUSES = {"pass", "fail", "inconclusive"}
SEVERITIES = {"none", "normal", "high"}
RESULT_REQUIRED_FIELDS = set(
    """
    schema_version case_id runtime runtime_version adapter adapter_version started_at
    duration_seconds prompt expected_skill acceptable_skills near_miss_skills
    must_not_trigger side_effect_allowed category selected_skill evidence_kind
    status severity reason score_notes prohibited_skill_hits raw_artifact
    """.split()  # noqa: SIM905 - compact to keep this helper under the file-size bar
)

DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "selected_skill": {"type": ["string", "null"]},
        "reason": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["selected_skill", "reason", "confidence"],
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def repo_paths(repo_root: Path) -> tuple[Path, Path, Path]:
    evals_dir = repo_root / "plugins" / "v1tamins" / "evals"
    return (
        evals_dir / "skill-routing.jsonl",
        evals_dir / "live-routing-output.schema.json",
        repo_root / ".v1tamins" / "live-routing",
    )


def load_fixture(repo_root: Path) -> list[dict[str, Any]]:
    fixture_path, _schema_path, _output_dir = repo_paths(repo_root)
    cases: list[dict[str, Any]] = []
    with fixture_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            case = json.loads(line)
            case["_line_number"] = line_number
            cases.append(case)
    return cases


def fixture_index(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(case["case_id"]): case for case in cases}


def filter_cases(
    cases: list[dict[str, Any]],
    *,
    case_ids: set[str] | None = None,
    categories: set[str] | None = None,
    expected_skill: str | None = None,
    max_cases: int | None = None,
) -> list[dict[str, Any]]:
    selected = []
    for case in cases:
        if case_ids and case["case_id"] not in case_ids:
            continue
        if categories and case["category"] not in categories:
            continue
        if expected_skill and case.get("expected_skill") != expected_skill:
            continue
        selected.append(case)
        if max_cases is not None and len(selected) >= max_cases:
            break
    return selected


def side_effect_skills(repo_root: Path) -> tuple[set[str] | None, list[str]]:
    skills_dir = repo_root / "plugins" / "v1tamins" / "skills"
    script = repo_root / "scripts" / "check-skill-metadata.rb"
    command = [
        "ruby",
        str(script),
        "--side-effect-skills-json",
        str(skills_dir),
        str(repo_root),
        "false",
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None, ["ruby is required to read skill metadata policy"]
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        return None, [f"skill metadata policy read failed: {detail}"]
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None, ["skill metadata policy output was not valid JSON"]
    if not isinstance(parsed, list) or not all(
        isinstance(item, str) for item in parsed
    ):
        return None, ["skill metadata policy output must be a JSON string array"]
    return set(parsed), []


def build_routing_prompt(case: dict[str, Any]) -> str:
    prompt = str(case["prompt"])
    return "\n".join(
        [
            "You are running a routing-only eval for v1tamins skills.",
            "Do not modify files, run commands, post comments, push commits, upload artifacts, or perform the requested workflow.",
            "Decide which v1-* skill the current runtime should select for the user request from its available skill metadata.",
            "If no v1tamins skill should run, set selected_skill to null.",
            "Return only JSON matching the requested schema.",
            "",
            "User request:",
            prompt,
        ]
    )


def runtime_bin(runtime: str, override: str | None = None) -> str | None:
    if override:
        return override
    return shutil.which(runtime)


def command_version(command: str, timeout: int) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr).strip()
    return result.returncode == 0, output or f"exit {result.returncode}"


def preflight_runtime(
    runtime: str,
    command: str | None,
    *,
    timeout: int,
    skip_auth_check: bool = False,
) -> tuple[bool, str, str]:
    if runtime not in RUNTIMES:
        return False, "", f"unknown runtime: {runtime}"
    if not command:
        return False, "", f"{runtime} binary not found"

    ok, version = command_version(command, timeout)
    if not ok:
        return False, version, f"{runtime} version check failed: {version}"

    if runtime == "claude" and not skip_auth_check:
        try:
            auth = subprocess.run(
                [command, "auth", "status", "--text"],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, version, f"claude auth status failed: {exc}"
        if auth.returncode != 0:
            detail = (auth.stdout or auth.stderr).strip() or f"exit {auth.returncode}"
            return False, version, f"claude auth unavailable: {detail}"

    return True, version, "ok"


def write_decision_schema(path: Path) -> None:
    path.write_text(json.dumps(DECISION_SCHEMA, indent=2) + "\n", encoding="utf-8")


def runtime_command(
    runtime: str,
    command: str,
    repo_root: Path,
    prompt: str,
    schema_path: Path,
) -> list[str]:
    if runtime == "codex":
        return [
            command,
            "exec",
            "--cd",
            str(repo_root),
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--json",
            "--output-schema",
            str(schema_path),
            prompt,
        ]

    return [
        command,
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--plugin-dir",
        str(repo_root / "plugins" / "v1tamins"),
        "--disallowedTools",
        "Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch",
        "--json-schema",
        json.dumps(DECISION_SCHEMA),
        prompt,
    ]


def json_from_text(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def skill_name_from_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"v1-[a-z0-9-]+", value)
    return match.group(0) if match else None


def skill_name_from_tool_use(event: dict[str, Any], runtime: str) -> str | None:
    if runtime == "codex":
        item = event.get("item")
        if not isinstance(item, dict):
            return None
        item_type = item.get("type")
        if item_type not in {"tool_call", "function_call"}:
            return None
        for field in ("name", "tool_name"):
            skill_name = skill_name_from_value(item.get(field))
            if skill_name:
                return skill_name
        input_value = item.get("input")
        if isinstance(input_value, dict):
            for field in ("skill", "skill_name", "name"):
                skill_name = skill_name_from_value(input_value.get(field))
                if skill_name:
                    return skill_name
        return None

    if runtime == "claude":
        content_blocks: list[Any] = []
        message = event.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                content_blocks.extend(content)
        if event.get("type") == "tool_use":
            content_blocks.append(event)

        for block in content_blocks:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            skill_name = skill_name_from_value(block.get("name"))
            if skill_name:
                return skill_name
            input_value = block.get("input")
            if isinstance(input_value, dict):
                for field in ("skill", "skill_name", "name"):
                    skill_name = skill_name_from_value(input_value.get(field))
                    if skill_name:
                        return skill_name
        return None

    return None


def decision_texts_from_event(event: dict[str, Any], runtime: str) -> list[str]:
    texts: list[str] = []
    if runtime == "codex":
        item = event.get("item")
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            texts.append(item["text"])
        return texts

    if runtime == "claude":
        if isinstance(event.get("result"), str):
            texts.append(event["result"])
        message = event.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        texts.append(block["text"])
        return texts

    return texts


def extract_decision(
    stdout: str, runtime: str
) -> tuple[str | None, str, str, float | None]:
    observed_skill: str | None = None
    decision: dict[str, Any] | None = None

    for line in stdout.splitlines():
        parsed = json_from_text(line)
        if parsed is None:
            continue

        observed_skill = observed_skill or skill_name_from_tool_use(parsed, runtime)

        if "selected_skill" in parsed:
            decision = parsed
            continue

        for text in decision_texts_from_event(parsed, runtime):
            maybe_decision = json_from_text(text)
            if maybe_decision and "selected_skill" in maybe_decision:
                decision = maybe_decision

    if observed_skill:
        return (
            observed_skill,
            "observed_invocation",
            "runtime emitted a skill-like event",
            None,
        )

    if decision is None:
        return None, "inconclusive", "no structured selected_skill result found", None

    selected = decision.get("selected_skill")
    if selected is not None and not isinstance(selected, str):
        selected = None
    reason = str(decision.get("reason", "structured routing decision"))
    confidence = decision.get("confidence")
    if not isinstance(confidence, (int, float)):
        confidence = None
    return (
        selected,
        "structured_decision",
        reason,
        float(confidence) if confidence is not None else None,
    )


def base_result(
    case: dict[str, Any],
    runtime: str,
    runtime_version: str,
    raw_artifact: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "case_id": case["case_id"],
        "runtime": runtime,
        "runtime_version": runtime_version,
        "adapter": f"{runtime}-cli",
        "adapter_version": ADAPTER_VERSION,
        "started_at": utc_now(),
        "duration_seconds": 0.0,
        "prompt": case["prompt"],
        "expected_skill": case.get("expected_skill"),
        "acceptable_skills": case.get("acceptable_skills", []),
        "near_miss_skills": case.get("near_miss_skills", []),
        "must_not_trigger": case.get("must_not_trigger", []),
        "side_effect_allowed": case.get("side_effect_allowed", False),
        "category": case.get("category"),
        "selected_skill": None,
        "evidence_kind": "inconclusive",
        "status": "inconclusive",
        "severity": "none",
        "reason": "",
        "score_notes": [],
        "prohibited_skill_hits": [],
        "raw_artifact": raw_artifact,
    }


def unavailable_result(
    case: dict[str, Any], runtime: str, reason: str
) -> dict[str, Any]:
    result = base_result(case, runtime, "", None)
    result["reason"] = reason
    result["score_notes"] = [reason]
    return result


def run_case(
    case: dict[str, Any],
    runtime: str,
    command: str | None,
    repo_root: Path,
    run_dir: Path,
    *,
    timeout: int,
    skip_auth_check: bool,
    dry_run: bool = False,
) -> dict[str, Any]:
    ok, version, detail = preflight_runtime(
        runtime, command, timeout=timeout, skip_auth_check=skip_auth_check
    )
    if not ok:
        return unavailable_result(case, runtime, detail)

    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{case['case_id']}-{runtime}.jsonl"
    raw_rel = str(raw_path.relative_to(run_dir))
    result = base_result(case, runtime, version, raw_rel)

    if dry_run:
        result["reason"] = "dry run; runtime was not launched"
        result["score_notes"] = ["dry run"]
        return result

    schema_path = run_dir / "routing-decision.schema.json"
    write_decision_schema(schema_path)
    prompt = build_routing_prompt(case)
    cmd = runtime_command(runtime, command or runtime, repo_root, prompt, schema_path)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        result["reason"] = f"{runtime} launch failed: {exc}"
        result["score_notes"] = [result["reason"]]
        return result

    result["duration_seconds"] = round(time.monotonic() - started, 3)
    raw_path.write_text(
        json.dumps(
            {
                "command": redact_command(cmd),
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if completed.returncode != 0:
        result["reason"] = process_failure_reason(runtime, completed)
        result["score_notes"] = [result["reason"]]
        return result

    selected, evidence_kind, reason, confidence = extract_decision(
        completed.stdout, runtime
    )
    result["selected_skill"] = selected
    result["evidence_kind"] = evidence_kind
    result["reason"] = reason
    if confidence is not None:
        result["confidence"] = confidence
    return result


def redact_command(command: list[str]) -> list[str]:
    redacted = []
    skip_next = False
    for part in command:
        if skip_next:
            redacted.append("<schema>")
            skip_next = False
            continue
        redacted.append(part)
        if part in {"--json-schema", "--output-schema"}:
            skip_next = True
    return redacted


def process_failure_reason(
    runtime: str, completed: subprocess.CompletedProcess[str]
) -> str:
    details = "\n".join(
        part.strip() for part in (completed.stderr, completed.stdout) if part.strip()
    )
    return f"{runtime} exited {completed.returncode}: {details[:500]}"


def validate_result_shape(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(RESULT_REQUIRED_FIELDS - set(result)):
        errors.append(f"missing field: {field}")
    if errors:
        return errors
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        errors.append("schema_version must be v1")
    if result["runtime"] not in RUNTIMES:
        errors.append("runtime must be codex or claude")
    if result["evidence_kind"] not in EVIDENCE_KINDS:
        errors.append("invalid evidence_kind")
    if result["status"] not in STATUSES:
        errors.append("invalid status")
    if result["severity"] not in SEVERITIES:
        errors.append("invalid severity")
    for field in (
        "acceptable_skills",
        "near_miss_skills",
        "must_not_trigger",
        "score_notes",
        "prohibited_skill_hits",
    ):
        if not isinstance(result[field], list):
            errors.append(f"{field} must be a list")
    if result["selected_skill"] is not None and not isinstance(
        result["selected_skill"], str
    ):
        errors.append("selected_skill must be a string or null")
    return errors


def score_result(
    result: dict[str, Any],
    fixture_case: dict[str, Any],
    side_effect_skill_names: set[str] | None,
    *,
    strict_inconclusive: bool = False,
) -> dict[str, Any]:
    selected = result.get("selected_skill")
    expected = fixture_case.get("expected_skill")
    acceptable = set(fixture_case.get("acceptable_skills", []))
    near_miss = set(fixture_case.get("near_miss_skills", []))
    must_not = set(fixture_case.get("must_not_trigger", []))
    notes: list[str] = []
    prohibited_hits: list[str] = []

    if result.get("evidence_kind") == "inconclusive":
        result["status"] = "fail" if strict_inconclusive else "inconclusive"
        result["severity"] = "normal" if strict_inconclusive else "none"
        result["score_notes"] = result.get("score_notes") or [
            "inconclusive runtime evidence"
        ]
        return result

    if isinstance(selected, str) and selected in must_not:
        prohibited_hits.append(selected)
        result["status"] = "fail"
        result["severity"] = (
            "high"
            if side_effect_skill_names is None or selected in side_effect_skill_names
            else "normal"
        )
        notes.append(f"selected prohibited skill {selected}")
        if side_effect_skill_names is None:
            notes.append("side-effect metadata unavailable; severity failed closed")
    elif expected is None and selected is None:
        result["status"] = "pass"
        result["severity"] = "none"
        notes.append("no skill selected for no-skill guardrail case")
    elif isinstance(expected, str) and selected == expected:
        result["status"] = "pass"
        result["severity"] = "none"
        notes.append("selected expected skill")
    elif isinstance(selected, str) and selected in acceptable:
        result["status"] = "pass"
        result["severity"] = "none"
        notes.append(f"selected acceptable alternative {selected}")
    elif isinstance(selected, str) and selected in near_miss:
        result["status"] = "fail"
        result["severity"] = "normal"
        notes.append(f"selected near-miss skill {selected}")
    elif selected is None:
        result["status"] = "fail"
        result["severity"] = "normal"
        notes.append("no skill selected when one was expected")
    else:
        result["status"] = "fail"
        result["severity"] = "normal"
        notes.append(f"unexpected selected skill {selected}")

    if prohibited_hits and not fixture_case.get("side_effect_allowed", False):
        notes.append("side effects were not allowed for this fixture case")
    result["prohibited_skill_hits"] = prohibited_hits
    result["score_notes"] = notes
    return result


def load_results(paths: list[Path]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            if (path / "results.jsonl").exists():
                candidates = [path / "results.jsonl"]
            else:
                candidates = sorted(path.glob("*.jsonl")) + sorted(path.glob("*.json"))
        else:
            candidates = [path]
        for candidate in candidates:
            text = candidate.read_text(encoding="utf-8")
            if candidate.suffix == ".jsonl":
                for line in text.splitlines():
                    if line.strip():
                        results.append(json.loads(line))
            else:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    results.extend(parsed)
                else:
                    results.append(parsed)
    return results


def summarize_results(results: list[dict[str, Any]]) -> str:
    by_status = Counter(result.get("status") for result in results)
    by_runtime = Counter(result.get("runtime") for result in results)
    by_evidence = Counter(result.get("evidence_kind") for result in results)
    high = sum(1 for result in results if result.get("severity") == "high")

    lines = [
        f"total: {len(results)}",
        "status: "
        + ", ".join(f"{name}={count}" for name, count in sorted(by_status.items())),
        "runtime: "
        + ", ".join(f"{name}={count}" for name, count in sorted(by_runtime.items())),
        "evidence: "
        + ", ".join(f"{name}={count}" for name, count in sorted(by_evidence.items())),
        f"high_severity_failures: {high}",
    ]
    failures = [result for result in results if result.get("status") == "fail"]
    for result in failures[:10]:
        lines.append(
            f"- {result['case_id']} [{result['runtime']}]: {result.get('reason', '')} "
            f"({' | '.join(result.get('score_notes', []))})"
        )
    return "\n".join(lines)
