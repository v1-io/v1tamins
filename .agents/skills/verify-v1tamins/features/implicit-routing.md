# Implicit routing

Implicit routing is the runtime choosing a `v1-*` skill from a plain user request using only the compact skill metadata. It is the plugin's central behavior and the reason descriptions are treated as runtime code.

## Sub-features

- `route-positive` selects the expected skill for a natural prompt.
- `route-near-miss` prefers the expected skill over a close neighbor.
- `route-budget` still routes when only the skill name and first description clause are visible.

## How to get to it (user POV)

- In Claude Code or Codex, describe the task in your own words without naming a skill, for example "Review this PR for bugs, regressions, and missing tests before merge."

## Driving it with verify-v1tamins

Preconditions:

- `python3 "$V" doctor` reports `drivable: true`.
- `V1_VERIFY_RUN_DIR` is exported.
- The case IDs below exist in `plugins/v1tamins/evals/skill-routing.jsonl` (`grep -c '"case_id": "<id>"'`).

- **Positive route (Claude).** Run `python3 "$V" route --runtime claude --case-id v1-deep-review-mergerisk-positive --max-cases 1`. `routing/run-*/results.jsonl` has one line with `runtime: claude`, `selected_skill: v1-deep-review`, `evidence_kind: structured_decision`, `status: pass`.
- **Positive route (Codex).** Run `python3 "$V" route --runtime codex --case-id v1-deep-review-mergerisk-positive --max-cases 1`. Same shape with `runtime: codex`.
- **Near miss.** Run `python3 "$V" route --runtime claude --case-id v1-menu-near-miss --max-cases 1`. `selected_skill` is `v1-skilling-it`, not `v1-menu`.
- **Budget stress.** Run `python3 "$V" route --runtime claude --case-id v1-menu-budget --max-cases 1`. `selected_skill` is `v1-menu`.
- **Proof.** Keep `routing/run-*/results.jsonl` and `summary.txt`. The runner's `raw/` holds the redacted command and stream per case.

## Gotchas

- The runner asks for a routing decision as JSON; `evidence_kind: structured_decision` is a judgement about selection, not an observed invocation. Explicit invocation is covered by the explicit-invoke feature.
- `inconclusive` with an auth message means the runtime was not driven. Fix login and rerun; never count it.
- Codex routes from the installed cache. A stale cache produces routing results for the old descriptions.
- Routing is model behavior and can vary. One failing case is a signal to rerun once and then inspect the description, not proof of a regression by itself.
