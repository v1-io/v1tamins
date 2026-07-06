# Skill Routing Evals

These files make autonomous skill selection reviewable. Runtime agents often
choose a skill from compact metadata before loading the full `SKILL.md`, so
description edits are behavior changes.

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

## Harness Quality Checklist

Use this checklist when reviewing whether a skill, routing rule, or runtime
adapter is failing because of the agent harness rather than the model alone.
Keep the review concrete: name the artifact under test, cite the fixture or
trace that proves the behavior, and decide which layer owns the fix.

| Layer | Responsibility | Review question | Common evidence |
| --- | --- | --- | --- |
| Orchestration | Decides which work steps should happen and in what order. | Did the agent choose a sensible workflow, stop point, and escalation boundary? | Plan/checklist drift, skipped required read, premature final answer, unsafe continuation. |
| Context | Assembles instructions and information that steer the model. | Did the prompt include the right repo, file, policy, source, and task state without stale or irrelevant baggage? | Missing AGENTS guidance, stale summaries, untrusted-source bleed-through, conflicting instructions. |
| Routing | Selects the runtime, model, skill, adapter, or provider that should handle the request. | Did the request land on the right skill or runtime path, and did near misses stay quiet? | `skill-routing.jsonl` cases, trigger inventory rows, live routing summaries. |
| Transport | Moves messages, tool calls, and streamed output reliably between components. | Did requests, responses, cancellation, retries, and partial output preserve intent and ordering? | Truncated payloads, duplicate sends, lost tool output, malformed JSON, timeout behavior. |
| State | Persists and resumes conversation, filesystem, git, cache, and task state. | Did the harness preserve the right state across turns, workers, model switches, or restarts? | Resume logs, dirty worktree checks, cached metadata, thread/worktree ids, replay evidence. |
| Execution | Lets the agent interact with the environment through tools. | Did tool contracts, permissions, validation, and error classes help the agent act correctly? | Exit codes, structured tool errors, permission denials, failed edits, lint/test proof. |

Apply the checklist as a diagnosis aid, not as a new mandatory gate. For small
skill metadata edits, the routing row plus `scripts/validate-plugin.sh` may be
enough. For runtime or adapter changes, cover all six layers before calling the
change verified.

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
