#!/usr/bin/env python3
"""Score normalized live skill-routing eval results against the static fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from skill_routing_live import (
    fixture_index,
    load_fixture,
    load_results,
    score_result,
    side_effect_skills,
    summarize_results,
    validate_result_shape,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score live routing eval result JSON/JSONL files."
    )
    parser.add_argument("results", nargs="+", help="result JSON/JSONL files or dirs")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--strict-inconclusive", action="store_true")
    parser.add_argument("--json", action="store_true", help="print scored JSONL")
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    cases = fixture_index(load_fixture(repo_root))
    side_effect_names = side_effect_skills(repo_root)
    results = load_results([Path(path) for path in args.results])
    scored = []
    errors = []

    for result in results:
        case_id = result.get("case_id")
        if case_id not in cases:
            errors.append(f"unknown case_id in result: {case_id}")
            continue
        scored_result = score_result(
            result,
            cases[case_id],
            side_effect_names,
            strict_inconclusive=args.strict_inconclusive,
        )
        shape_errors = validate_result_shape(scored_result)
        if shape_errors:
            errors.append(f"{case_id}: {', '.join(shape_errors)}")
        scored.append(scored_result)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.json:
        for result in scored:
            print(json.dumps(result, sort_keys=True))
    else:
        print(summarize_results(scored))

    return 1 if any(result["status"] == "fail" for result in scored) else 0


if __name__ == "__main__":
    raise SystemExit(run())
