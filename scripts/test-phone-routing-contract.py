#!/usr/bin/env python3
"""Static contract checks for the explicit Phone-a-Friend workflow."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/SKILL.md"
METADATA = ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/agents/openai.yaml"
RUNNER = ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/scripts/peer-run.sh"
ENV = ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/scripts/peer-env.sh"
TEMPLATES = (
    ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/references/command-templates.md"
)
ROUTING = ROOT / "plugins/v1tamins/evals/skill-routing.jsonl"


def main() -> int:
    skill = SKILL.read_text(encoding="utf-8")
    metadata = METADATA.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    env = ENV.read_text(encoding="utf-8")
    templates = TEMPLATES.read_text(encoding="utf-8")

    checks = {
        "frontmatter disables implicit invocation": "disable-model-invocation: true"
        in skill,
        "skill requires confirmation": "confirmation_required" in skill,
        "skill links dynamic selection": "references/model-selection.md" in skill,
        "skill links auth wrapper": "scripts/peer-env.sh" in skill,
        "metadata is explicit-only": "allow_implicit_invocation: false" in metadata
        and "invocation_posture: explicit_only" in metadata,
        "runner closes stdin": "</dev/null" in runner,
        "runner has deadline": "deadline-seconds" in runner and "timed_out" in runner,
        "runner emits typed JSON": '"schema":"v1-peer-run/v1"' in runner,
        "runner has no pattern kill": "pkill -f" not in runner
        and "killall" not in runner,
        "environment wrapper scrubs keys": "OPENAI_API_KEY" in env
        and "ANTHROPIC_API_KEY" in env,
        "templates use environment wrapper": "peer-env.sh" in templates,
        "cursor closes stdin": 'PHONE_A_FRIEND_PROMPT" < /dev/null' in templates,
        "automatic retry is forbidden": "does not auto-retry or replace" in skill
        and "do not retry or substitute automatically" in templates,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        for name in failed:
            print(f"FAIL: {name}")
        return 1

    cases = [
        json.loads(line)
        for line in ROUTING.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    phone_cases = [
        case
        for case in cases
        if "v1-phone-a-friend"
        in {
            case["expected_skill"],
            *case["must_not_trigger"],
            *case["near_miss_skills"],
        }
    ]
    if not any(
        case["expected_skill"] == "v1-phone-a-friend"
        and "/v1-phone-a-friend" in case["prompt"]
        for case in phone_cases
    ):
        print("FAIL: missing explicit Phone-a-Friend positive fixture")
        return 1
    if not any(
        case["expected_skill"] is None
        and "v1-phone-a-friend" in case["must_not_trigger"]
        for case in phone_cases
    ):
        print("FAIL: missing implicit Phone-a-Friend negative fixture")
        return 1

    print("Phone-a-Friend routing contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
