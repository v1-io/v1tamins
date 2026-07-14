#!/usr/bin/env python3
"""Run bounded fresh-session behavior evals for v1-skilling-it."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _skilling_it_behavior_cases import (
    CASE_ID_PATTERN,
    contained_path,
    execution_receipt_matches,
    load_execution_expectations,
    seed_files,
    validate_case,
)
from _skilling_it_behavior_judge import (
    claude_result,
    judge_prompt,
    process_reason,
    run_judge,
    verdict_error,
)
from _skilling_it_behavior_support import (
    CHILD_ENV_NAMES,
    append_private,
    artifact_report,
    bounded_artifacts,
    capture_snapshot,
    child_env,
    claude_permission_args,
    claude_sandbox_prefix,
    claude_scope_probe,
    codex_thread_id,
    extract_tool_events,
    initial_prompt,
    inventory,
    markdown_verdict,
    mutation_passed,
    normalized_tool_calls,
    observed_file_read,
    read_optional,
    rendered_command,
    run_process,
    run_synthetic_command,
    stage_plugin,
    support_self_test,
    tree_digest,
    write_private,
)
from skill_routing_live import runtime_bin

CASE_START = "<!-- behavior-cases:start -->"
CASE_END = "<!-- behavior-cases:end -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the committed v1-skilling-it workflow matrix."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--runtime", action="append", choices=["codex", "claude"], default=[]
    )
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--output-dir")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--codex-bin")
    parser.add_argument("--claude-bin")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run deterministic adapter evidence checks without launching a runtime",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    try:
        body = text.split(CASE_START, 1)[1].split(CASE_END, 1)[0]
    except IndexError as exc:
        raise ValueError("behavior matrix markers are missing") from exc
    lines = [line for line in body.splitlines() if line.lstrip().startswith("{")]
    cases = [json.loads(line) for line in lines]
    seen: set[str] = set()
    for case in cases:
        validate_case(case)
        case_id = case["case_id"]
        if (
            not isinstance(case_id, str)
            or not CASE_ID_PATTERN.fullmatch(case_id)
            or case_id in seen
        ):
            raise ValueError(f"invalid or duplicate case_id: {case_id!r}")
        seen.add(case_id)
    if not cases:
        raise ValueError("behavior matrix contains no cases")
    return cases


def transcript(turns: list[str]) -> str:
    return "\n\n".join(
        f"Assistant turn {index}:\n{text}" for index, text in enumerate(turns, 1)
    )


def failed_conversation(
    result: subprocess.CompletedProcess[str],
    turns: list[str],
    partial: str,
    fallback: str,
) -> tuple[str, str, str]:
    if partial:
        turns.append(partial)
    response = transcript(turns)
    outcome = "failed_assessable" if response.strip() else "unavailable"
    return outcome, response, process_reason(result, fallback)


def run_conversation(
    runtime: str,
    command: str,
    case: dict[str, Any],
    workspace: Path,
    staged_plugin: Path,
    case_dir: Path,
    prompt: str,
    timeout: int,
    targets: dict[str, Path],
    target_state: dict[str, dict[str, str]],
    command_argv: list[str],
    snapshots: list[dict[str, Any]],
    tool_events: list[dict[str, Any]],
) -> tuple[str, str, str]:
    destination = workspace / "destination"
    reply_updates = case.get("reply_updates", [])
    turns: list[str] = []
    raw_path = case_dir / "runtime.jsonl"
    write_private(raw_path, "")

    def record(result: subprocess.CompletedProcess[str], label: str) -> None:
        append_private(raw_path, result.stdout + result.stderr)
        tool_events.extend(extract_tool_events(result.stdout))
        write_private(
            case_dir / "tool-events.jsonl",
            "".join(json.dumps(event, sort_keys=True) + "\n" for event in tool_events),
        )
        snapshots.append(
            capture_snapshot(case_dir, label, workspace, targets, target_state)
        )

    def apply_turn_updates(update_index: int, label: str) -> None:
        if update_index < len(reply_updates):
            seed_files(destination, reply_updates[update_index])
        target_updates = case.get("synthetic_target_updates", [])
        if update_index < len(target_updates):
            for name, state in target_updates[update_index].items():
                target_state[name].update(state)
        snapshots.append(
            capture_snapshot(case_dir, label, workspace, targets, target_state)
        )

    if runtime == "codex":
        response_path = case_dir / "turn-01.md"
        args = [
            command,
            "exec",
            "--cd",
            str(workspace),
            "--sandbox",
            "read-only" if case["mutation"] == "none" else "workspace-write",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "--json",
            "--output-last-message",
            str(response_path),
            prompt,
        ]
        result = run_process(args, workspace, timeout)
        record(result, "turn-01")
        if result.returncode != 0:
            return failed_conversation(
                result, turns, read_optional(response_path), "runtime launch failed"
            )
        thread_id = codex_thread_id(result.stdout)
        if not thread_id:
            partial = read_optional(response_path)
            if partial:
                turns.append(partial)
            return (
                "failed_assessable" if turns else "unavailable",
                transcript(turns),
                "codex did not return a thread id",
            )
        turns.append(read_optional(response_path))
        for index, reply in enumerate(case["replies"], start=2):
            update_index = index - 2
            apply_turn_updates(update_index, f"turn-{index:02d}-pre")
            response_path = case_dir / f"turn-{index:02d}.md"
            resumed = run_process(
                [
                    command,
                    "exec",
                    "resume",
                    thread_id,
                    "--skip-git-repo-check",
                    "--ignore-user-config",
                    "--ignore-rules",
                    "--json",
                    "--output-last-message",
                    str(response_path),
                    str(reply),
                ],
                workspace,
                timeout,
            )
            record(resumed, f"turn-{index:02d}")
            if resumed.returncode != 0:
                return failed_conversation(
                    resumed,
                    turns,
                    read_optional(response_path),
                    "runtime resume failed",
                )
            turns.append(read_optional(response_path))
    else:
        common = [
            "--safe-mode",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--no-session-persistence",
            "--output-format",
            "stream-json",
            "--verbose",
            *claude_permission_args(case, workspace, staged_plugin),
            "--plugin-dir",
            str(staged_plugin),
        ]
        prefix = claude_sandbox_prefix(command, workspace, [workspace], [staged_plugin])
        result = run_process(
            [*prefix, "-p", *common, prompt],
            workspace,
            timeout,
        )
        record(result, "turn-01")
        if result.returncode != 0:
            return failed_conversation(
                result, turns, claude_result(result.stdout), "runtime launch failed"
            )
        turns.append(claude_result(result.stdout))
        for update_index, reply in enumerate(case["replies"]):
            apply_turn_updates(update_index, f"turn-{update_index + 2:02d}-pre")
            continuation = "\n\n".join(
                [
                    "Continue this synthetic behavior-evaluation conversation.",
                    "Original user request:\n" + prompt,
                    "Conversation so far:\n" + transcript(turns),
                    "Latest user reply:\n" + str(reply),
                    (
                        "Respond to the latest reply and continue the workflow. Re-read any "
                        "relevant workspace state; do not repeat completed mutations unless the "
                        "latest reply explicitly authorizes them."
                    ),
                ]
            )
            resumed = run_process(
                [*prefix, "-p", *common, continuation],
                workspace,
                timeout,
            )
            record(resumed, f"turn-{update_index + 2:02d}")
            if resumed.returncode != 0:
                return failed_conversation(
                    resumed,
                    turns,
                    claude_result(resumed.stdout),
                    "runtime continuation failed",
                )
            turns.append(claude_result(resumed.stdout))
    return (
        "completed",
        transcript(turns),
        "ok",
    )


def uncovered_runtime_cases(
    results: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    runtimes: list[str],
) -> list[str]:
    passed = {
        (item["runtime"], item["case_id"])
        for item in results
        if item["status"] == "pass"
    }
    return [
        f"{runtime}/{case['case_id']}"
        for runtime in runtimes
        for case in cases
        if (runtime, case["case_id"]) not in passed
    ]


def run_self_test() -> int:
    criterion = {"id": "c1", "passed": True, "evidence": "observed"}
    good_verdict = {"criteria": [criterion], "summary": "passed"}
    duplicate_verdict = dict(good_verdict)
    duplicate_verdict["criteria"] = [criterion, criterion]
    env_ok = all(
        name in CHILD_ENV_NAMES or name.startswith("LC_") for name in child_env()
    )
    mixed_runtime_results = [
        {"runtime": "claude", "case_id": "example", "status": "pass"},
        {"runtime": "codex", "case_id": "example", "status": "inconclusive"},
    ]
    runtime_coverage_ok = uncovered_runtime_cases(
        mixed_runtime_results,
        [{"case_id": "example"}],
        ["claude", "codex"],
    ) == ["codex/example"]
    if not (
        verdict_error(good_verdict, 1) is None
        and verdict_error(duplicate_verdict, 1) is not None
        and env_ok
        and runtime_coverage_ok
        and support_self_test()
    ):
        print("ERROR: adapter evidence self-test failed", file=sys.stderr)
        return 1
    print("ok: adapter evidence, filesystem scope, and permissions are isolated")
    return 0


def run_case(
    runtime: str,
    command: str | None,
    case: dict[str, Any],
    skill_dir: Path,
    source_digest: str,
    plugin_dir: Path,
    run_dir: Path,
    timeout: int,
    dry_run: bool,
    execution_expectation: dict[str, Any] | None = None,
    isolation_reason: str | None = None,
) -> dict[str, Any]:
    case_dir = contained_path(run_dir / runtime, case["case_id"])
    case_dir.mkdir(parents=True, mode=0o700)
    case_dir.chmod(0o700)
    workspace = case_dir / "workspace"
    destination = workspace / "destination"
    staged_plugin = workspace / "staged-v1tamins-plugin"
    destination.mkdir(parents=True, mode=0o700)
    targets: dict[str, Path] = {}
    target_state: dict[str, dict[str, str]] = {}
    for name, fixture in case.get("synthetic_targets", {}).items():
        target = contained_path(workspace / "targets", name)
        target.mkdir(parents=True, mode=0o700)
        seed_files(target, fixture["initial_files"])
        targets[name] = target
        target_state[name] = {"readback": fixture["readback"]}
    staged_skill = stage_plugin(plugin_dir, skill_dir, staged_plugin)
    staged_digest = tree_digest(staged_skill)
    if source_digest != staged_digest:
        raise RuntimeError("staged v1-skilling-it digest differs from current checkout")
    seed_files(destination, case["initial_files"], case.get("initial_file_modes"))
    command_argv = rendered_command(case, destination)
    execution_receipt = (
        run_synthetic_command(command_argv, destination, timeout)
        if command and not dry_run and not isolation_reason
        else {}
    )
    prompt = initial_prompt(case, destination, staged_skill, targets, execution_receipt)
    write_private(case_dir / "prompt.md", prompt + "\n")
    before_destination = inventory(destination)
    before = inventory(workspace, exclude_top={"staged-v1tamins-plugin"})
    write_private(case_dir / "before-files.txt", before)
    snapshots = [
        capture_snapshot(case_dir, "turn-00", workspace, targets, target_state)
    ]
    tool_events: list[dict[str, Any]] = []

    response = ""
    runtime_outcome = "unavailable"
    reason = "dry run; runtime not launched"
    verdict: dict[str, Any] | None = None
    if isolation_reason:
        reason = isolation_reason
    elif not dry_run and command:
        runtime_outcome, response, reason = run_conversation(
            runtime,
            command,
            case,
            workspace,
            staged_plugin,
            case_dir,
            prompt,
            timeout,
            targets,
            target_state,
            command_argv,
            snapshots,
            tool_events,
        )
    elif not command:
        reason = f"{runtime} binary not found"
    write_private(case_dir / "response.md", response + ("\n" if response else ""))
    after_destination = inventory(destination)
    after = inventory(workspace, exclude_top={"staged-v1tamins-plugin"})
    write_private(case_dir / "after-files.txt", after)
    report = artifact_report(destination)
    allowed_top = {"destination", "staged-v1tamins-plugin"}
    if targets:
        allowed_top.add("targets")
    unexpected = sorted(
        path.name for path in workspace.iterdir() if path.name not in allowed_top
    )
    tool_calls = normalized_tool_calls(tool_events)
    staged_read = observed_file_read(tool_events, staged_skill / "SKILL.md")
    target_mutations = {
        name: sum(
            call["name"] in {"Write", "Edit"}
            and isinstance(call["input"].get("file_path"), str)
            and Path(call["input"]["file_path"])
            .resolve()
            .is_relative_to(target.resolve())
            for call in tool_calls
        )
        for name, target in targets.items()
    }
    target_content_matches = {
        name: tree_digest(target) == tree_digest(destination)
        for name, target in targets.items()
    }
    existing_source_unchanged = (
        not targets
        or not case["initial_files"]
        or before_destination == after_destination
    )
    execution_ok = execution_receipt_matches(
        execution_receipt, command_argv, execution_expectation or {}
    )
    staged_unchanged = tree_digest(staged_skill) == staged_digest
    mechanical = {
        "artifact_report": report,
        "artifact_required": case["mutation"] == "required",
        "execution_receipt": execution_receipt,
        "execution_expectation": execution_expectation or {},
        "execution_receipt_valid": execution_ok,
        "runtime_read_staged_skill": staged_read,
        "staged_skill_unchanged": staged_unchanged,
        "target_mutation_counts": target_mutations,
        "target_content_matches_source": target_content_matches,
        "existing_source_unchanged_during_deployment": existing_source_unchanged,
        "unexpected_workspace_entries": unexpected,
    }
    mechanical_ok = (
        report["passed"]
        and not unexpected
        and (report["checked"] or case["mutation"] != "required")
        and execution_ok
        and staged_unchanged
        and (not targets or all(count == 1 for count in target_mutations.values()))
        and (not targets or all(target_content_matches.values()))
        and existing_source_unchanged
    )
    artifacts = bounded_artifacts({"destination": destination, **targets})
    judge_input = judge_prompt(
        case,
        response,
        before_destination,
        after_destination,
        snapshots,
        artifacts,
        mechanical,
        tool_calls,
    )
    write_private(case_dir / "judge-input.md", judge_input + "\n")
    if runtime_outcome in {"completed", "failed_assessable"}:
        verdict, judge_reason = run_judge(
            runtime, command, case, judge_input, workspace, case_dir, timeout
        )
        if verdict is None:
            reason = (
                judge_reason
                if runtime_outcome == "completed"
                else f"{reason}; judge: {judge_reason}"
            )
        elif runtime_outcome == "completed":
            reason = verdict["summary"]
        else:
            reason = f"{reason}; judge: {verdict['summary']}"
    mutation_ok = mutation_passed(
        case["mutation"], before_destination, after_destination
    )

    if runtime_outcome == "failed_assessable":
        status = "fail"
    elif verdict is None:
        status = "fail" if runtime_outcome == "completed" else "inconclusive"
    elif (
        mutation_ok
        and mechanical_ok
        and staged_read
        and all(item["passed"] for item in verdict["criteria"])
    ):
        status = "pass"
    else:
        status = "fail"
    result = {
        "schema_version": "v1",
        "case_id": case["case_id"],
        "runtime": runtime,
        "runtime_outcome": runtime_outcome,
        "status": status,
        "mutation_rule": case["mutation"],
        "mutation_check": "pass" if mutation_ok else "fail",
        "source_digest": source_digest,
        "source_provenance": {
            "staged_current_checkout_digest_verified": source_digest == staged_digest,
            "runtime_read_evidence": (
                "observed_structured_tool_event" if staged_read else "not_observed"
            ),
        },
        "mechanical_check": "pass" if mechanical_ok else "fail",
        "mechanical_evidence": mechanical,
        "reason": reason,
        "criteria": [] if verdict is None else verdict["criteria"],
    }
    write_private(case_dir / "verdict.md", markdown_verdict(result))
    return result


def run() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    if args.max_cases < 0:
        print("ERROR: --max-cases must be zero or greater", file=sys.stderr)
        return 2
    repo_root = Path(args.repo_root).resolve()
    matrix = repo_root / "plugins" / "v1tamins" / "evals" / "skilling-it-behavior.md"
    expectation_path = (
        repo_root
        / "plugins"
        / "v1tamins"
        / "evals"
        / "skilling-it-execution-expectations.json"
    )
    skill_dir = repo_root / "plugins" / "v1tamins" / "skills" / "v1-skilling-it"
    plugin_dir = repo_root / "plugins" / "v1tamins"
    source_digest = tree_digest(skill_dir)
    try:
        cases = load_cases(matrix)
        execution_expectations = load_execution_expectations(expectation_path, cases)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    selected_ids = set(args.case_id)
    if selected_ids:
        cases = [case for case in cases if case["case_id"] in selected_ids]
        unknown = selected_ids - {case["case_id"] for case in cases}
        if unknown:
            print(f"ERROR: unknown case ids: {sorted(unknown)}", file=sys.stderr)
            return 2
    if args.max_cases:
        cases = cases[: args.max_cases]
    if not cases:
        print("ERROR: no behavior cases selected", file=sys.stderr)
        return 2
    runtimes = args.runtime or ["codex", "claude"]
    output_root = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else repo_root / ".v1tamins" / "behavior" / "v1-skilling-it"
    )
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = output_root / f"run-{timestamp}"
    run_dir.mkdir(parents=True, mode=0o700)
    run_dir.chmod(0o700)
    commands = {
        "codex": runtime_bin("codex", args.codex_bin),
        "claude": runtime_bin("claude", args.claude_bin),
    }
    claude_isolation_reason: str | None = None
    codex_isolation_reason = None
    if "codex" in runtimes and not args.dry_run:
        codex_isolation_reason = (
            "Codex live behavior is unavailable: this adapter cannot prove a "
            "workspace-only read boundary for Codex"
        )
    if "claude" in runtimes and commands["claude"] and not args.dry_run:
        isolated, detail = claude_scope_probe(
            commands["claude"], run_dir, min(args.timeout, 120)
        )
        if not isolated:
            claude_isolation_reason = f"Claude isolation preflight failed: {detail}"
    results = []
    for case in cases:
        for runtime in runtimes:
            results.append(
                run_case(
                    runtime,
                    commands[runtime],
                    case,
                    skill_dir,
                    source_digest,
                    plugin_dir,
                    run_dir,
                    args.timeout,
                    args.dry_run,
                    execution_expectations.get(case["case_id"]),
                    claude_isolation_reason
                    if runtime == "claude"
                    else codex_isolation_reason,
                )
            )
    results_path = run_dir / "results.jsonl"
    write_private(
        results_path,
        "".join(json.dumps(result, sort_keys=True) + "\n" for result in results),
    )
    counts = {
        status: sum(item["status"] == status for item in results)
        for status in ("pass", "fail", "inconclusive")
    }
    uncovered = uncovered_runtime_cases(results, cases, runtimes)
    summary = (
        "\n".join(
            [
                "# v1-skilling-it Behavior Summary",
                "",
                f"- Pass: {counts['pass']}",
                f"- Fail: {counts['fail']}",
                f"- Inconclusive: {counts['inconclusive']}",
                f"- Runtime cases without a pass: {', '.join(uncovered) or 'none'}",
                f"- Results: `{results_path}`",
            ]
        )
        + "\n"
    )
    write_private(run_dir / "summary.md", summary)
    print(f"results: {results_path}")
    print(summary, end="")
    if args.dry_run:
        return 0
    return 1 if counts["fail"] or uncovered else 0


if __name__ == "__main__":
    raise SystemExit(run())
