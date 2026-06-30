# Skill Routing Evals

These files make autonomous skill selection reviewable. Runtime agents often
choose a skill from compact metadata before loading the full `SKILL.md`, so
description edits are behavior changes.

## Files

- `trigger-inventory.md` records each packaged skill's trigger contract, likely
  natural prompts, near-miss neighbors, side-effect posture, and budget risk.
- `skill-routing.jsonl` contains routing cases used by
  `scripts/check-skill-routing-fixture.py`.

## JSONL Schema

Each line in `skill-routing.jsonl` is one JSON object with:

- `case_id`: stable lowercase slug
- `prompt`: user-style prompt, without naming the skill unless that is the case
  being tested
- `expected_skill`: the `v1-*` skill that should win, or `null` for no-skill
  guardrail cases
- `acceptable_skills`: other skills that are acceptable secondary routes
- `near_miss_skills`: skills that are close but should not be preferred
- `must_not_trigger`: skills that should not run for this prompt
- `side_effect_allowed`: whether the prompt clearly permits external mutation
- `prompt_source`: one of `research_seed`, `repo_overlap`, `runtime_budget`,
  `side_effect_guard`, or `contributor_seed`
- `budget_stress`: whether the case should remain routeable from the skill name
  plus the first description clause
- `category`: one of `positive`, `near_miss`, `negative`, `overlap`,
  `side_effect`, or `budget`
- `rationale`: short explanation of the routing boundary

## Contribution Rule

When changing a skill name, description, `agents/openai.yaml`, invocation
policy, or routing-relevant body guidance, update both the trigger inventory and
the JSONL fixture. Add at least one positive case and one near-miss or negative
case for any new skill.

Run:

```bash
scripts/validate-plugin.sh --verbose
```

The static fixture is not a replacement for fresh-session Codex or Claude Code
benchmarks. It is the cheap review gate that keeps trigger contracts from
drifting between live eval runs.
