# Skill Routing Evals

These files make autonomous skill selection reviewable. Runtime agents often
choose a skill from compact metadata before loading the full `SKILL.md`, so
description edits are behavior changes.

Description contract: keep `SKILL.md` frontmatter descriptions non-empty and
target 180 characters or fewer. Include only the skill's core purpose and
distinct natural trigger phrases. Keep methods, outputs, edge cases, and
neighbor boundaries in the loaded body or a directly linked reference.

Invocation contract: `policy.invocation_posture` is `implicit`,
`selective_implicit`, or `explicit_only`. The package has no `agent-only`
posture. Explicit parent workflows stay explicit even when their children are
model-selectable.

## Files

- `trigger-inventory.md` records each packaged skill's trigger contract, likely
  natural prompts, near-miss neighbors, side-effect posture, and budget risk.
- `skill-routing.jsonl` contains routing cases used by
  `scripts/check-skill-routing-fixture.py`.
- `live-routing-output.schema.json` defines the normalized output for optional
  live routing runs.
- `agents/openai.yaml` on each skill records machine-readable invocation policy:
  `policy.invocation_posture` is `implicit`, `selective_implicit`, or
  `explicit_only`; `policy.side_effects` records routing-critical side effects
  such as `external_write`, `git_remote`, `peer_launch`, and `browser_capture`.

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
case for any new skill. Add a `category: side_effect` case for every skill with
non-empty `policy.side_effects`.

Run:

```bash
scripts/validate-plugin.sh --verbose
```

## Live Routing Evals

The static fixture is the required CI-safe contract. It proves that trigger
expectations are complete, side-effect aware, and internally consistent.

Live routing evals are optional smoke checks for real runtime behavior. They may
make model calls, require local Codex or Claude Code authentication, and produce
local transcripts, so they are not part of `scripts/validate-plugin.sh`.

The runner strips API-key and auth-token environment variables from Codex and
Claude child processes. Live evals are intended to exercise the local CLI
login/subscription state, not direct API-key billing.

Run a small sample after changing skill descriptions, invocation posture,
high-overlap fixture cases, or side-effect policy:

```bash
scripts/run-skill-routing-live-eval.py --runtime codex --max-cases 3
scripts/run-skill-routing-live-eval.py --runtime claude --category side_effect --max-cases 2
```

The runner writes local artifacts under `.v1tamins/live-routing/`, which is
ignored by git. Share the summary or selected normalized results in a PR, not
raw transcripts.

Score existing result files without launching runtimes:

```bash
scripts/score-skill-routing-live-eval.py .v1tamins/live-routing/run-*/results.jsonl
```

Interpret results as:

- `pass`: selected the expected skill or an acceptable alternative.
- `fail`: selected a near-miss, unexpected, or prohibited skill.
- `inconclusive`: runtime, auth, adapter, or output parsing did not provide
  enough evidence. Missing runtime/auth is not a static fixture failure.

Evidence classes matter. `observed_invocation` means the adapter saw a concrete
skill-like runtime event. `structured_decision` means the runtime returned a
routing decision in the requested JSON shape. `inconclusive` means no reliable
decision was available.

## v1-skilling-it Behavior Adapter

Routing evidence proves selection, not workflow execution. The committed
[`skilling-it-behavior.md`](skilling-it-behavior.md) matrix and
`scripts/run-skilling-it-behavior-eval.py` exercise the multi-turn authoring
contract in isolated synthetic workspaces.

The adapter stages the current skill into each case, scripts user replies,
inventories only the declared `destination/`, and asks a separate fresh judge
for a structured verdict. It writes ignored evidence under
`.v1tamins/behavior/v1-skilling-it/`. Case directories and files use restrictive
local permissions. Do not use private inputs, credentials, customer data, or
production destinations.

```bash
scripts/run-skilling-it-behavior-eval.py --runtime codex
scripts/run-skilling-it-behavior-eval.py --runtime claude --case-id audit-read-only
scripts/run-skilling-it-behavior-eval.py --runtime codex --dry-run
scripts/run-skilling-it-behavior-eval.py --self-test
```

Interpret `inconclusive` as missing evidence, never success. Raw prompts,
responses, inventories, and verdicts may contain model output; retain them only
for the review window, then delete the run directory documented by the matrix.
