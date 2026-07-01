#!/usr/bin/env python3
"""Run opt-in live routing eval cases against Codex and/or Claude Code."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from skill_routing_live import (
    filter_cases,
    fixture_index,
    load_fixture,
    repo_paths,
    run_case,
    runtime_bin,
    score_result,
    side_effect_skills,
    summarize_results,
    validate_result_shape,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run selected v1tamins routing fixture cases against live runtimes."
    )
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument(
        "--runtime",
        action="append",
        choices=["codex", "claude", "both"],
        default=[],
        help="runtime to evaluate; repeatable",
    )
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--expected-skill")
    parser.add_argument(
        "--max-cases",
        type=int,
        default=5,
        help="maximum fixture cases to run after filters; use 0 for no limit",
    )
    parser.add_argument("--output-dir", help="defaults to .v1tamins/live-routing")
    parser.add_argument("--codex-bin")
    parser.add_argument("--claude-bin")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-auth-check",
        action="store_true",
        help="skip preflight auth checks and let runtime launch failures be inconclusive",
    )
    parser.add_argument(
        "--strict-inconclusive",
        action="store_true",
        help="score inconclusive adapter output as failure",
    )
    parser.add_argument(
        "--no-fail-on-routing-failure",
        action="store_true",
        help="exit 0 even when scored live results fail",
    )
    return parser.parse_args()


def selected_runtimes(values: list[str]) -> list[str]:
    if not values:
        return ["codex", "claude"]
    runtimes: set[str] = set()
    for value in values:
        if value == "both":
            runtimes.update({"codex", "claude"})
        else:
            runtimes.add(value)
    return sorted(runtimes)


def run() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    _fixture_path, _schema_path, default_output = repo_paths(repo_root)
    output_root = Path(args.output_dir).resolve() if args.output_dir else default_output
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = output_root / f"run-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    cases = filter_cases(
        load_fixture(repo_root),
        case_ids=set(args.case_id) or None,
        categories=set(args.category) or None,
        expected_skill=args.expected_skill,
        max_cases=None if args.max_cases == 0 else args.max_cases,
    )
    if not cases:
        print("ERROR: no fixture cases matched filters", file=sys.stderr)
        return 2

    case_by_id = fixture_index(cases)
    side_effect_names = side_effect_skills(repo_root)
    results_path = run_dir / "results.jsonl"
    summary_path = run_dir / "summary.txt"
    runtimes = selected_runtimes(args.runtime)
    commands = {
        "codex": runtime_bin("codex", args.codex_bin),
        "claude": runtime_bin("claude", args.claude_bin),
    }

    results = []
    for case in cases:
        for runtime in runtimes:
            result = run_case(
                case,
                runtime,
                commands[runtime],
                repo_root,
                run_dir,
                timeout=args.timeout,
                skip_auth_check=args.skip_auth_check,
                dry_run=args.dry_run,
            )
            result = score_result(
                result,
                case_by_id[result["case_id"]],
                side_effect_names,
                strict_inconclusive=args.strict_inconclusive,
            )
            shape_errors = validate_result_shape(result)
            if shape_errors:
                result["status"] = "fail"
                result["severity"] = "normal"
                result["score_notes"] = [f"result shape invalid: {shape_errors}"]
            results.append(result)

    with results_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True) + "\n")

    summary = summarize_results(results)
    summary_path.write_text(summary + "\n", encoding="utf-8")
    print(f"results: {results_path}")
    print(f"summary: {summary_path}")
    print(summary)

    if args.no_fail_on_routing_failure:
        return 0
    return 1 if any(result["status"] == "fail" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(run())
