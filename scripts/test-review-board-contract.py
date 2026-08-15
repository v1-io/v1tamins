#!/usr/bin/env python3
"""Static contract checks for proposal-gated Review Board behavior."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/v1tamins/skills/v1-review-board/SKILL.md"
CONTRACT = (
    ROOT / "plugins/v1tamins/skills/v1-review-board/references/review-contract.md"
)
EXAMPLE = ROOT / "plugins/v1tamins/skills/v1-review-board/references/example-run.md"
METADATA = ROOT / "plugins/v1tamins/skills/v1-review-board/agents/openai.yaml"


def main() -> int:
    skill = SKILL.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    example = EXAMPLE.read_text(encoding="utf-8")
    metadata = METADATA.read_text(encoding="utf-8")
    checks = {
        "board requires preflight": "dynamic discovery and prompt-resolution preflight"
        in skill,
        "board requires explicit roster": "confirmation_required" in skill
        and "No selection means zero launches" in contract,
        "board defaults to quality proposal": "`quality` roster" in skill
        and "quality" in contract,
        "board defaults to ledger": "Default autonomy is **`ledger`**" in skill
        and "**default `ledger`**" in contract,
        "board separates apply": "`apply` and `full-auto` are separate explicit choices"
        in skill,
        "board has no default model IDs": "Do not hardcode model names" in contract
        and "model_unresolved" in contract,
        "board records prompt digest": "source digest" in contract
        and "prompt source" in example,
        "board forbids fallback fanout": "Do not automatically retry, replace, or add a peer"
        in skill,
        "board scopes no-retry to after dispatch": "After dispatch" in skill
        and "After dispatch" in contract,
        "board shares the dispatch boundary": "pre_dispatch_failed" in skill
        and "pre_dispatch_failed" in contract
        and "dispatch_state" in contract
        and "v1-phone-a-friend" in contract,
        "board allows one bounded pre-dispatch repair": "one bounded repair"
        in skill
        and "bounded repair of the same seat" in contract,
        "board metadata remains explicit": "invocation_posture: explicit_only"
        in metadata
        and "allow_implicit_invocation: false" in metadata,
        "example shows zero-launch gate": "no peer has launched yet" in example,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        for name in failed:
            print(f"FAIL: {name}")
        return 1
    print("Review Board contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
