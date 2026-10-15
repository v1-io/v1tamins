# Explicit invocation

Explicit invocation is a user naming a skill with `/v1-<name>` and getting an answer shaped by that skill's body. `v1-menu` is the probe because it is explicit-only, read-only, and its contract is observable: recommend one skill, name the runner-up, say why, mark explicit skills.

## Sub-features

- `invoke-menu-claude` expands `/v1-menu` in headless Claude Code and answers per the menu contract.
- `invoke-menu-codex` does the same in Codex from the installed cache.
- `invoke-menu-structured` returns the recommendation as JSON fields when a schema is supplied.

## How to get to it (user POV)

- In Claude Code type `/v1-menu <situation>`.
- In Codex type `/v1-menu <situation>` or `$v1-menu <situation>`.

## Driving it with verify-v1tamins

Preconditions:

- `python3 "$V" doctor` reports `drivable: true`.
- `V1_VERIFY_RUN_DIR` is exported.
- `S=.agents/skills/verify-v1tamins/scripts/menu-recommendation.schema.json`.

- **Invoke in Claude.** Run `python3 "$V" claude --label menu --expect-skill v1-menu '/v1-menu which v1 skill fits: "review this branch for merge risk before I open the PR". Name one skill and the runner-up.'`. The summary has `expected_skill_loaded: true`, `status: pass`, and `final_text` naming `/v1-deep-review` first with one runner-up and a reason.
- **Invoke in Codex.** Run `python3 "$V" codex --label menu '/v1-menu which v1 skill fits: "review this branch for merge risk before I open the PR". Name one skill and the runner-up.'`. The summary has `turn_completed: true`, `tool_calls: []`, and `final_text` naming `v1-deep-review` first.
- **Structured answer.** Run `python3 "$V" claude --label menu-json --expect-skill v1-menu --schema "$S" '/v1-menu which v1 skill fits: "review this branch for merge risk before I open the PR".'`. `structured_output.recommended_skill` names `v1-deep-review` (the model may keep the leading slash) and `runner_up` names one other `v1-*` skill.
- **Proof.** Keep `menu.claude.summary.json`, `menu.codex.summary.json`, and the raw streams. The prompt and the answer sit in the same file.

## Gotchas

- No runtime emits a Skill tool-use event for a `/v1-*` prompt in headless mode; the body is injected before the first model turn. Do not wait for `tool_uses` to prove invocation.
- `--expect-skill` proves the skill was listed, not that it was followed. Read `final_text`.
- A long-lived Claude session with the same plugin installed may answer differently from the checkout; always drive through the helper so `--plugin-dir` applies.
- Codex waits on stdin when it is a pipe; the helper closes stdin. Running `codex exec` by hand without `< /dev/null` hangs.
