#!/usr/bin/env python3
"""Validate the v1tamins skill-routing fixture and trigger inventory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {
    "case_id",
    "prompt",
    "expected_skill",
    "acceptable_skills",
    "near_miss_skills",
    "must_not_trigger",
    "side_effect_allowed",
    "prompt_source",
    "budget_stress",
    "category",
    "rationale",
}

VALID_CATEGORIES = {
    "positive",
    "near_miss",
    "negative",
    "overlap",
    "side_effect",
    "budget",
}

VALID_PROMPT_SOURCES = {
    "research_seed",
    "repo_overlap",
    "runtime_budget",
    "side_effect_guard",
    "contributor_seed",
}

VALID_INVOCATION_POSTURES = {
    "implicit",
    "selective_implicit",
    "explicit_only",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate plugins/v1tamins/evals/skill-routing.jsonl"
    )
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def load_skill_names(skills_dir: Path) -> list[str]:
    return sorted(
        path.name
        for path in skills_dir.glob("v1-*")
        if path.is_dir() and not path.name.startswith("v1-_")
    )


def load_side_effect_skill_names(skills_dir: Path) -> list[str]:
    """Read the simple policy block used by agents/openai.yaml files."""
    side_effect_skills: list[str] = []

    for skill_dir in sorted(skills_dir.glob("v1-*")):
        if not skill_dir.is_dir() or skill_dir.name.startswith("v1-_"):
            continue

        openai_yaml = skill_dir / "agents" / "openai.yaml"
        if not openai_yaml.exists():
            continue

        policy = parse_openai_policy(openai_yaml)
        side_effects = policy.get("side_effects", [])
        if side_effects:
            side_effect_skills.append(skill_dir.name)

    return side_effect_skills


def parse_openai_policy(path: Path) -> dict[str, Any]:
    """Parse the small policy subset needed for fixture coverage checks.

    Full YAML validation happens in scripts/validate-plugin.sh via Ruby. This
    parser intentionally handles only scalar fields and simple list fields under
    the top-level `policy:` key so the fixture checker stays dependency-free.
    """
    policy: dict[str, Any] = {}
    current_list_key: str | None = None
    in_policy = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))

        if indent == 0:
            in_policy = stripped == "policy:"
            current_list_key = None
            continue

        if not in_policy:
            continue

        if indent == 2 and stripped.endswith(":"):
            current_list_key = stripped[:-1]
            policy[current_list_key] = []
            continue

        if indent == 2 and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_list_key = None
            value = value.strip()
            if value in {"true", "false"}:
                policy[key] = value == "true"
            else:
                policy[key] = value.strip("\"'")
            continue

        if indent == 4 and current_list_key and stripped.startswith("- "):
            value = stripped[2:].strip().strip("\"'")
            if value:
                policy[current_list_key].append(value)

    posture = policy.get("invocation_posture")
    if posture is not None and posture not in VALID_INVOCATION_POSTURES:
        return {}

    return policy


def require_list_of_strings(
    case: dict[str, Any], field: str, errors: list[str]
) -> list[str]:
    value = case.get(field)
    case_id = case.get("case_id", "<unknown>")
    if not isinstance(value, list):
        errors.append(f"{case_id}: {field} must be a list")
        return []

    bad_values = [item for item in value if not isinstance(item, str) or not item]
    if bad_values:
        errors.append(f"{case_id}: {field} must contain only non-empty strings")
        return []

    return value


def validate_skill_ref(
    case_id: str,
    field: str,
    skill: str,
    skill_names: set[str],
    errors: list[str],
) -> None:
    if skill not in skill_names:
        errors.append(f"{case_id}: {field} references unknown skill {skill!r}")


def validate_case(
    case: dict[str, Any],
    line_number: int,
    skill_names: set[str],
    errors: list[str],
) -> None:
    case_id = case.get("case_id", f"line {line_number}")

    missing = sorted(REQUIRED_FIELDS.difference(case))
    if missing:
        errors.append(f"{case_id}: missing required field(s): {', '.join(missing)}")
        return

    if not isinstance(case["case_id"], str) or not case["case_id"].strip():
        errors.append(f"line {line_number}: case_id must be a non-empty string")
    elif not re.match(r"^[a-z0-9][a-z0-9._-]*$", case["case_id"]):
        errors.append(f"{case_id}: case_id must be lowercase slug text")

    if not isinstance(case["prompt"], str) or len(case["prompt"].strip()) < 8:
        errors.append(f"{case_id}: prompt must be a meaningful string")

    expected_skill = case["expected_skill"]
    if expected_skill is not None:
        if not isinstance(expected_skill, str) or not expected_skill:
            errors.append(f"{case_id}: expected_skill must be a skill name or null")
        else:
            validate_skill_ref(
                case_id, "expected_skill", expected_skill, skill_names, errors
            )

    for field in ("acceptable_skills", "near_miss_skills", "must_not_trigger"):
        for skill in require_list_of_strings(case, field, errors):
            validate_skill_ref(case_id, field, skill, skill_names, errors)

    for field in ("side_effect_allowed", "budget_stress"):
        if not isinstance(case[field], bool):
            errors.append(f"{case_id}: {field} must be boolean")

    if case["category"] not in VALID_CATEGORIES:
        errors.append(
            f"{case_id}: category must be one of {', '.join(sorted(VALID_CATEGORIES))}"
        )

    if case["prompt_source"] not in VALID_PROMPT_SOURCES:
        errors.append(
            f"{case_id}: prompt_source must be one of {', '.join(sorted(VALID_PROMPT_SOURCES))}"
        )

    if not isinstance(case["rationale"], str) or len(case["rationale"].strip()) < 12:
        errors.append(f"{case_id}: rationale must explain the routing decision")

    if expected_skill is None and not case["must_not_trigger"]:
        errors.append(f"{case_id}: no-skill cases must name must_not_trigger skills")

    if case["category"] == "budget" and not case["budget_stress"]:
        errors.append(f"{case_id}: budget category requires budget_stress=true")

    if (
        case["category"] == "side_effect"
        and case["expected_skill"]
        and not (case["side_effect_allowed"] or case["must_not_trigger"])
    ):
        errors.append(
            f"{case_id}: side_effect case must either allow side effects or guard a skill"
        )


def load_fixture(
    path: Path, skill_names: set[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    cases: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()

    if not path.exists():
        return cases, [f"missing routing fixture: {path}"]

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                case = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc.msg}")
                continue

            if not isinstance(case, dict):
                errors.append(
                    f"{path}:{line_number}: each JSONL line must be an object"
                )
                continue

            case_id = case.get("case_id")
            if isinstance(case_id, str):
                if case_id in seen_ids:
                    errors.append(f"{case_id}: duplicate case_id")
                seen_ids.add(case_id)

            validate_case(case, line_number, skill_names, errors)
            cases.append(case)

    return cases, errors


def validate_coverage(
    cases: list[dict[str, Any]],
    skill_names: list[str],
    side_effect_skill_names: list[str],
) -> list[str]:
    errors: list[str] = []
    positive: Counter[str] = Counter()
    guardrail: Counter[str] = Counter()
    budget: Counter[str] = Counter()
    side_effect: Counter[str] = Counter()

    for case in cases:
        expected_skill = case.get("expected_skill")
        if isinstance(expected_skill, str):
            positive[expected_skill] += 1
            if case.get("budget_stress") is True:
                budget[expected_skill] += 1

        for skill in case.get("near_miss_skills", []):
            guardrail[skill] += 1
        for skill in case.get("must_not_trigger", []):
            guardrail[skill] += 1

        if case.get("category") == "side_effect":
            if isinstance(expected_skill, str):
                side_effect[expected_skill] += 1
            for skill in case.get("acceptable_skills", []):
                side_effect[skill] += 1
            for skill in case.get("must_not_trigger", []):
                side_effect[skill] += 1

    for skill in skill_names:
        if positive[skill] == 0:
            errors.append(f"{skill}: missing positive expected_skill fixture case")
        if guardrail[skill] == 0:
            errors.append(f"{skill}: missing negative or near-miss fixture coverage")
        if budget[skill] == 0:
            errors.append(f"{skill}: missing budget_stress fixture case")

    for skill in side_effect_skill_names:
        if side_effect[skill] == 0:
            errors.append(f"{skill}: missing side_effect fixture coverage")

    return errors


def validate_trigger_inventory(path: Path, skill_names: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing trigger inventory: {path}"]

    content = path.read_text(encoding="utf-8")
    errors: list[str] = []

    for skill in skill_names:
        if f"| `{skill}` |" not in content:
            errors.append(f"{skill}: missing trigger-inventory row")

    return errors


def print_summary(cases: list[dict[str, Any]], verbose: bool) -> None:
    if not verbose:
        return

    by_category: defaultdict[str, int] = defaultdict(int)
    budget_cases = 0
    for case in cases:
        by_category[str(case.get("category"))] += 1
        if case.get("budget_stress") is True:
            budget_cases += 1

    print(f"ok: {len(cases)} routing fixture cases")
    for category in sorted(by_category):
        print(f"ok: {category} cases: {by_category[category]}")
    print(f"ok: budget-stress cases: {budget_cases}")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    skills_dir = repo_root / "plugins" / "v1tamins" / "skills"
    evals_dir = repo_root / "plugins" / "v1tamins" / "evals"
    fixture_path = evals_dir / "skill-routing.jsonl"
    inventory_path = evals_dir / "trigger-inventory.md"

    skill_names = load_skill_names(skills_dir)
    skill_name_set = set(skill_names)
    side_effect_skill_names = load_side_effect_skill_names(skills_dir)

    errors: list[str] = []
    cases, fixture_errors = load_fixture(fixture_path, skill_name_set)
    errors.extend(fixture_errors)
    if not cases:
        errors.append(f"{fixture_path}: no routing fixture cases")
    else:
        errors.extend(validate_coverage(cases, skill_names, side_effect_skill_names))
    errors.extend(validate_trigger_inventory(inventory_path, skill_names))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print_summary(cases, args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
