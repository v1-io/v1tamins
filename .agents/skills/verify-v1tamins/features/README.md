# v1tamins verification map

This directory is the maintained source for verifying the user-facing behavior
of the v1tamins plugin: a runtime loads the package, a user invokes or is
routed to one `v1-*` skill, and the answer follows that skill's contract. Read
this index before driving, then use the matching feature file as the recipe.

## Baseline preconditions

- Work from the checkout root with a clean `plugins/v1tamins/`.
- `claude` and `codex` are on `PATH` and logged in with a local account.
- `python3 "$V" doctor` reports `drivable: true`, where
  `V=.agents/skills/verify-v1tamins/scripts/verify-v1tamins.py`.
- `export V1_VERIFY_RUN_DIR="$(python3 "$V" new-run)"` so every command in one
  verification shares one evidence directory.
- Codex drives the installed cache, so Doctor's `installed_verification` must
  be `match`. Claude drives the checkout through `--plugin-dir`.
- Never drive an interactive session the user or another agent has open; every
  recipe spawns its own headless turn.

## Driving conventions

- Prompts are literal. Keep the `/v1-<name>` form and the quoted user request
  unchanged so results stay comparable across runs.
- Stable handles are skill directory names (`v1-<name>`), slash names, and
  routing fixture `case_id` values. Never grep answers for the skill's
  internal headings.
- Run Claude drives through `python3 "$V" claude`, Codex drives through
  `python3 "$V" codex`, routing through `python3 "$V" route`.
- Drives are read-only by default. Do not pass `--allow-writes` unless the
  feature under test must write, and then say so in the report.

## Proof and skip reporting

- Load proof is the init `skills` listing (Claude) or `verification_status:
  match` (Codex) in the summary, not the model's claim that a skill exists.
- Invocation proof is the prompt plus `final_text` or `structured_output`
  judged against the invoked skill's contract.
- Routing proof is the `results.jsonl` line: `status`, `selected_skill`,
  `evidence_kind`. `inconclusive` is missing evidence, never a pass.
- Record the feature ID and runtime with every claim.
- Report an unreachable path with the attempted command and the unmet
  precondition (for example `codex is not logged in`). Do not report a
  Codex path as verified because the Claude path passed.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the
user-visible behavior, then exactly four H2 sections in this order:
`Sub-features`, `How to get to it (user POV)`, `Driving it with
verify-v1tamins` (starting with `Preconditions:` and pairing each user action
with an exact command and observable result), and `Gotchas`.

## Features

- [Plugin load](./plugin-load.md) covers the package loading into Claude Code
  from the checkout and into Codex from the installed cache with every skill.
- [Explicit invocation](./explicit-invoke.md) covers a user typing
  `/v1-menu` and getting a recommendation in both runtimes.
- [Implicit routing](./implicit-routing.md) covers a natural request selecting
  the expected skill from compact metadata.
- [Side-effect guard](./side-effect-guard.md) covers explicit-only and
  side-effectful skills staying unselected unless the user names them.
