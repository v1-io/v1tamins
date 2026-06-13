---
name: v1-loop-engineering
description: Use when turning a product idea, implementation task, agent workflow, automation, or prompt into a bounded goal-verification loop. Triggers on "loop engineering", "bounded implementation loop", "agent loop", "recursive goal", "turn this into a loop", "design the loop".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - AskUserQuestion
---
# Loop Engineering

Design a bounded implementation loop before giving an agent open-ended work.

Use this skill when the useful unit is not a single prompt or static plan, but a repeatable cycle: discover, change, verify, learn, and either continue or stop. The goal is to make the loop small enough to execute safely and concrete enough to evaluate.

## Quick Start

Return this loop contract before implementation:

```markdown
## Loop Contract

### Goal
[One observable outcome.]

### Scope
- Editable: [files, folders, artifact, or prompt surface]
- Read-only context: [sources allowed for discovery]
- Out of scope: [mutations, systems, users, or broad refactors excluded]

### Cycle
1. Inspect the current state.
2. Make one focused change.
3. Run the live verification command or check.
4. Self-review the changed surface.
5. Record the result.
6. Keep, adjust, revert, or stop.

### Verification
- Primary proof: [command, test, review checklist, screenshot, or artifact]
- Regression guard: [what must not get worse]
- Evidence format: [table, notes file, PR body section, or terminal output]

### Stop Rules
- Stop when: [success condition]
- Stop early if: [risk, uncertainty, failure pattern, or budget limit]
- Max cycles: [number]
```

If the user asked for implementation and the contract is concrete, execute the first cycle after writing the contract. If the contract has unresolved safety, scope, or verification gaps, stop and ask only the blocking question.

For architecture or refactor loops, default to this shape:

```markdown
Loop: Refactor [surface] until [architecture quality bar], while preserving [behavior proof].
Verification: run [test/lint/typecheck/manual proof] after every meaningful change.
Self-review: check for needless abstractions, scattered special cases, weak names, and hidden behavior changes.
Progress log: keep a short cycle table in chat, the PR body, or a temporary notes file.
Commit checkpoint: commit only kept cycles, after verification and self-review pass.
```

## Workflow

### 1. Name the Loop

Write the loop's job in one sentence:

```markdown
Loop: Improve [target] until [observable condition], without [excluded risk].
```

Prefer a narrow target:

- Good: "Reduce flaky failures in this Playwright spec until it passes three consecutive local runs."
- Good: "Refine this PR description until it matches the diff and cites verification evidence."
- Too broad: "Improve the app."
- Too broad: "Make the agent smarter."

### 2. Bound the Surface

Define the loop boundary before changing anything:

| Boundary | Question |
| --- | --- |
| Editable surface | What can the agent modify? |
| Read-only context | What can the agent inspect for discovery? |
| External effects | What writes, sends, deploys, purchases, or data mutations are forbidden? |
| Budget | How many cycles, minutes, or attempts are allowed? |
| Human gate | What decision needs user approval before continuing? |

Keep the editable surface as small as possible. Prefer one file, one folder, one prompt, one workflow, one test, or one artifact over a repo-wide loop.

### 3. Choose Verification First

Pick the proof before designing the cycle.

Useful proof types:

- Command proof: a test, lint, typecheck, benchmark, validation script, or dry-run.
- Artifact proof: a rendered file, generated report, screenshot, diff, or checklist.
- Review proof: a short rubric applied to the output when no executable check exists.
- User proof: a small prototype test, interview synthesis, or observed behavior.

Do not start a loop whose success can only be judged by vibes. If no proof exists, make the first cycle create the smallest proof surface.

For implementation loops, run live verification after every meaningful step rather than saving verification for the end. A meaningful step is any change that could alter behavior, architecture, generated output, routing, data shape, prompt behavior, or user-visible state.

### 4. Make the Cycle Single-Variable

Each cycle should change one thing:

1. Inspect enough context to choose the next move.
2. State the hypothesis for the change.
3. Make one focused edit or action.
4. Verify immediately.
5. Self-review the changed surface.
6. Decide: keep, adjust, revert, or stop.

Avoid combining strategy changes. A cycle that changes code, tests, prompts, and configuration at once cannot teach the next cycle what mattered.

Self-review before keeping a cycle:
- Does the change preserve the contract and permission boundary?
- Did the change make the design simpler, or just move complexity?
- Did the change add a special case that belongs in a clearer model?
- Is the verification result fresh and specific to this cycle?
- Is the next cycle still inside the original editable surface?

### 5. Keep a Cycle Log

Use this format in chat, a notes file, or the PR body:

```markdown
| Cycle | Hypothesis | Change | Live proof | Self-review | Decision | Next |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [why this should help] | [one focused change] | [command/result] | [quality check] | Keep/Revert/Adjust/Stop | [next move] |
```

Keep the log brief. Its job is to prevent repeated attempts, hidden regressions, and unbounded wandering.

For longer autonomous runs, keep the log in a workspace-local or temporary notes file named for the project. Do not rely on memory or terminal scrollback as the only progress record.

### 6. Commit Checkpoints

When the user asked for commits or the workflow expects resumable checkpoints, commit only after the cycle is kept:

1. Verify the change.
2. Self-review the diff.
3. Stage only the intended files.
4. Commit with a message that explains why the kept cycle improved the result.

Do not commit discarded cycles, speculative edits, failed verification, private notes, secrets, or local-only artifacts.

### 7. Stop Deliberately

Stop the loop when one of these is true:

- The success condition is met.
- The same failure repeats after two focused attempts.
- Verification is unavailable or unreliable.
- The next cycle would cross the permission boundary.
- The remaining work is a product decision, not an implementation decision.
- The cycle budget is spent.

When stopping before success, return the cycle log and the smallest blocking question or follow-up option.

## Output Modes

### Planning Mode

Use when the user asks to design a loop but not execute it:

```markdown
## Loop Contract
[contract]

## First Three Cycles
| Cycle | Hypothesis | Change | Proof | Stop/Continue Signal |
| --- | --- | --- | --- | --- |

## Risks
- [Boundary, proof, or safety risk.]
```

### Execution Mode

Use when the user asks to run the loop:

```markdown
## Loop Contract
[contract]

## Cycle Log
| Cycle | Hypothesis | Change | Live proof | Self-review | Decision | Next |
| --- | --- | --- | --- | --- | --- | --- |

## Current State
[Done, stopped, or needs approval.]
```

## Anti-Patterns

- Starting implementation before naming the proof.
- Letting "iterate" mean unlimited attempts.
- Expanding the editable surface after a failed cycle.
- Treating discovery, implementation, verification, and shipping as one cycle.
- Using a loop to avoid a product decision.
- Continuing after verification becomes stale, flaky, or unavailable.
- Recording only successes and losing the failed attempts that should shape the next cycle.

## Chaining

- Use `v1-bare-bones` first when the proposed loop is too broad.
- Use `v1-prd` first when the loop lacks a product decision or acceptance criteria.
- Use `v1-autoresearch-skill` when the loop has a numeric metric and should run as an optimization process.
- Use `v1-testing-prototypes` when the verification proof depends on target-user behavior.
- Use `v1-pr` after a bounded implementation loop produces a verified diff.
