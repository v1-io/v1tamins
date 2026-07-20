---
name: v1-implement-unit
description: Use when the user explicitly asks to implement one planned ticket or unit through a mergeable pull request. Triggers on "implement unit", "implement this ticket end to end", "/v1-implement-unit", or "take this unit to a mergeable PR".
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - Skill
  - Agent
  - AskUserQuestion
---

# Implement Unit

Orchestrate one planned unit from implementation through independent review and a mergeable PR. Keep implementation, review, and orchestration in separate execution contexts.

## Usage

```text
/v1-implement-unit <ticket>
/v1-implement-unit <ticket> plan:<path>
```

Codex invocation:

```text
$v1-implement-unit <ticket>
```

This workflow creates threads, writes code, pushes commits, opens or updates a PR, and replies to review feedback. Run only after explicit user invocation.

## Roles

- **Orchestrator:** remain in the invoking thread. Check the plan, launch threads, transfer artifacts, monitor progress, enforce gates, notify the user. Do not implement or remediate code here.
- **Implementation thread:** own one writable isolated checkout, branch, implementation, tests, commits, review remediation, and PR landing.
- **Review thread:** start fresh and read-only for one exact head SHA. Run `v1-review-board` with `autonomy:ledger`. Never edit, commit, or push.

A thread means a host-provided isolated, resumable task, thread, or agent context that the orchestrator can monitor and message. Record its handle. If the host cannot create, monitor, and message separate resumable contexts, stop; do not collapse the workflow into the orchestrator thread.

## Workflow

### 1. Resolve the unit and plan

Resolve the exact ticket or unit. Find its plan in this order:

1. An explicit `plan:<path>` argument.
2. A plan linked or embedded in the ticket.
3. A repository plan that names the exact ticket or stable unit ID.
4. A plan supplied in the current conversation.

Treat a ticket body as the plan only when it passes the adequacy gate below. Do not combine unrelated notes into an inferred plan.

Require all of these:

- one bounded outcome plus scope boundaries or non-goals;
- acceptance criteria or definition of done;
- an actionable implementation approach or implementation units;
- verification criteria covering the changed behavior;
- no unresolved decision that materially changes the solution.

For an artifact carrying `artifact_contract: ce-unified-plan/v1`, require `artifact_readiness: implementation-ready` and `execution: code`. Reject requirements-only, knowledge-work, progress-like readiness values, and unclassified execution.

After the gate passes, normalize the selected plan to one immutable plan artifact accessible to spawned threads. If the plan exists only in a ticket or conversation, copy its exact content and source identifier to host scratch space outside the tracked repository. Do not invent missing fields or commit the scratch artifact.

**Hard stop:** if no adequate plan exists, do not launch a thread, edit code, change ticket state, or open a PR. Report the missing plan fields and the exact planning handoff needed. Recommend `ce-plan <plan-path>` when that skill and a requirements artifact are available.

### 2. Preflight the orchestration

After the plan passes:

1. Confirm the host can create, monitor, and message separate resumable contexts.
2. Confirm `v1-review-board` and `v1-land-pr` are callable in spawned contexts. Stop if either required skill is unavailable.
3. Check whether the compound-engineering `ce-work` skill is callable. Record `available` or `unavailable`; absence is not a blocker.
4. Resolve the repository, intended base branch, starting SHA, dirty state, and any existing branch or PR for the unit. Preserve unrelated changes.
5. Create a progress checklist for implementation, review cycles, and landing.

### 3. Launch implementation

Create one writable implementation thread in an isolated checkout. Give it:

- ticket or unit ID;
- plan path and the relevant plan sections;
- repository, base branch, starting SHA, branch, and dirty-state constraints;
- acceptance criteria, scope boundaries, verification contract, and repository instructions;
- the requirement to return status, thread handle, checkout, branch, head SHA, changed files, commits, verification evidence, blockers, and PR URL when present.

When `ce-work` is available, instruct the implementation thread to invoke:

```text
ce-work mode:return-to-caller <plan-path>
```

Return-to-caller mode is mandatory: this orchestrator owns review and landing. If `ce-work` is unavailable, instruct the thread to implement the plan and run local verification without starting its own review or PR tail.

Require a committed, locally verified head before review. Do not review a moving or uncommitted diff.

### 4. Monitor implementation

Wait on compact progress snapshots. Keep the implementation thread alive for later remediation.

- Continue waiting while progress is observable.
- Surface a material user decision; do not answer it on the user's behalf.
- Treat `blocked` or `failed` as a stop unless the thread provides a safe, plan-consistent recovery.
- Verify the returned branch, head SHA, changed files, commits, and tests against repository state before review.

### 5. Run a clean review cycle

For each implementation head:

1. Freeze the exact `base SHA...head SHA` review target.
2. Create a fresh read-only review thread with no implementation conversation history and no writable implementation checkout.
3. Give it the plan, acceptance criteria, repository instructions, exact refs, and PR URL when present.
4. Invoke `v1-review-board` with `autonomy:ledger`. Explicitly forbid apply, commit, push, and GitHub mutation.
5. Require at least one surviving peer plus a locally verified ledger. A zero-peer board is blocked, not clean.
6. Require the result to state `clean`, `findings`, or `blocked`, the reviewed head SHA, peer status, and every verified finding with severity, file and line, evidence, and disposition.

`clean` means no verified actionable finding remains. Invalid, duplicate, or demonstrably out-of-scope suggestions may be recorded as non-actionable. An unresolved valid `Fix`, `Partial`, or `Defer` finding is not clean.

### 6. Hand findings back and repeat

When findings exist:

1. Send the verified ledger and reviewed head SHA to the existing implementation thread.
2. Require narrow remediation, relevant tests, a commit, and a new head SHA.
3. Require evidence for rejected findings; do not silently dismiss them.
4. Start a new clean review thread against the new immutable head.

Repeat until clean. Do not reuse a review thread between SHAs.

Stop as blocked when the same valid finding returns without head advancement or new evidence, the implementation thread cannot remediate within plan scope, or progress otherwise stalls. Report the loop state instead of cycling forever.

### 7. Land the PR

After a clean review, tell the implementation thread to invoke `v1-land-pr` on the reviewed branch. Require it to:

- reuse or create the PR against the resolved base;
- monitor required checks through completion;
- inventory issue comments, review summaries, inline review threads, and check annotations after every push;
- address actionable feedback from every human and bot actor, including Copilot, Codex, Datadog, and any repository-specific reviewer;
- reply to addressed feedback and resolve eligible conversations;
- report unsupported APIs or feedback it cannot resolve;
- stop after the remediation limit defined by `v1-land-pr` rather than churn speculative fixes.

Any landing remediation that changes code invalidates the clean review SHA. Return to Step 5 for the new head, then resume `v1-land-pr`.
Keep one cumulative remediation-push count across every landing resume. Do not reset the limit by re-invoking the skill after a review cycle.

### 8. Verify mergeable state and stop

Do not merge the PR. Stop only after a final live check proves:

- the PR is open and ready for review, not draft;
- the head SHA is the clean-reviewed SHA;
- no merge conflict exists;
- all required checks pass;
- no change-requested review or unresolved actionable human/bot feedback remains;
- one final feedback sweep found no new actionable item.

If branch protection still needs human approval, an external check, or another unavailable action, report `blocked`, not `mergeable`.

Notify the user with:

- ticket or unit and plan path;
- implementation thread handle;
- review cycle count and final reviewed SHA;
- PR URL, base and head branches, mergeability, and checks;
- bot/human feedback status;
- validation evidence and any remaining user action.

Then stop.

## Guardrails

- Implement exactly one ticket or plan unit. Stop on discovered adjacent work.
- Preserve unrelated and untracked files.
- Never let the review thread mutate the implementation checkout or PR.
- Never claim clean review for a SHA that changed afterward.
- Never treat a polling timeout as failure while checks show progress.
- Never claim all feedback addressed without querying every available review surface.
- Never merge, force-push, bypass branch protection, or approve a PR on the user's behalf.
