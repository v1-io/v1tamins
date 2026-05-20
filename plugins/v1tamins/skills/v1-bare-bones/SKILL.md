---
name: v1-bare-bones
description: Use when a plan, PRD, proposal, or implementation outline is overscoped, too ambitious for the immediate goal, or needs to be reduced to a bare-bones version. Triggers on "bare bones", "no damn whistles", "no bells and whistles", "strip this plan", "trim this plan", "scope creep", "descope this plan", "MVP only".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - AskUserQuestion
---
# Bare Bones

Strip an overscoped plan down to the smallest useful version.

Use this skill when the user wants less plan, less architecture, less ceremony, and no speculative extras. The job is not to make the plan more impressive. The job is to make it shippable.

## Quick Start

1. Read the plan and any directly referenced context.
2. State the plan's single intended outcome in one sentence.
3. Treat every proposed item as out of scope by default.
4. Promote only items required for the first useful delivery.
5. Return a replacement bare-bones plan and a cut/defer ledger.

## Core Technique: Won't-First Scoping

Start from "Won't Have this time," then justify every promotion.

Promote an item to the bare-bones plan only when it passes at least one of these tests:

- **Usability:** Without it, the result cannot be used for the stated outcome.
- **Correctness:** Without it, the result is misleading, broken, unsafe, or corrupts data.
- **Validation:** Without it, there is no credible way to know whether the work succeeded.
- **Dependency:** Without it, another kept item cannot be implemented.
- **No workaround:** There is no acceptable manual, temporary, or existing workaround for the first slice.

If an item is valuable but does not pass one of these tests, defer it. If it is ornamental, speculative, or included only because it seems nice, cut it.

## Workflow

### 1. Load the Plan

Read the supplied plan, PRD, proposal, ticket, or implementation outline. If the plan references a specific local file, read that file. If it references nearby repo context and that context affects scope, inspect only the smallest relevant context.

Do not expand the plan while gathering context. Look for the original outcome, hidden dependencies, and evidence that a proposed item is truly required.

### 2. Name the Outcome

State the intended outcome in one sentence:

```markdown
Outcome: [the smallest observable result this work needs to produce]
```

If the plan has multiple outcomes, choose the one the user asked for most directly. Move the others to deferred scope unless the user explicitly asked for a multi-outcome plan.

### 3. Build the Scope Ledger

Classify each meaningful plan item:

| Bucket | Meaning |
| --- | --- |
| Keep | Required for first useful delivery |
| Cut | Not needed, ornamental, duplicate, or speculative |
| Defer | Valuable later, but not required now |
| Question | Blocks trimming because the required outcome is ambiguous |

Keep the ledger concise. Group related items instead of listing every tiny subtask.

### 4. Apply the Must-Have Test

Challenge every Keep item:

- Would the task fail or be unusable without this?
- Would the user cancel the first delivery if this were missing?
- Is the workaround impossible, unsafe, or more expensive than doing it now?
- Is this needed in the first vertical slice?
- Is this required for safety, correctness, privacy, or basic verification?

If the answer is no, downgrade the item to Defer or Cut.

### 5. Rewrite the Plan

Produce a replacement plan with only these sections:

```markdown
## Bare-Bones Plan

### Goal
[One sentence]

### Build
- [Smallest implementation step]
- [Smallest implementation step]

### Verify
- [Smallest meaningful validation]

### Non-Goals
- [Explicitly excluded item]
- [Explicitly excluded item]

### Blocking Questions
- [Only questions that must be answered before implementation]
```

Omit `Blocking Questions` when there are none. Do not include roadmap, future phases, rollout ceremony, dashboards, analytics, polish, or platform architecture unless one is required for the first useful delivery.

### 6. Edit Only When Asked

If the user asks to update a plan file, edit the existing artifact in place. Preserve the original heading style when possible, but replace bloated sections with the bare-bones plan.

If the user only asks for a review or trim, return the revised plan in chat and do not edit files.

## What To Cut Aggressively

Cut or defer these unless they pass the Must-have test:

- Generic "future-proofing"
- New abstractions without immediate reuse
- Extra configuration surfaces
- Optional dashboards, metrics, reports, or screenshots
- Polished UI states beyond the first usable flow
- Broad test matrices when one focused regression test proves the slice
- Documentation beyond the minimum needed to operate or review the change
- Migration, rollout, or monitoring ceremony for a local-only or low-risk change
- Nice-to-have refactors near the work
- Alternative implementations kept "just in case"

## Output Format

Use this format:

```markdown
Outcome: [one sentence]

## Bare-Bones Plan

### Goal
[one sentence]

### Build
- [...]

### Verify
- [...]

### Non-Goals
- [...]

## Scope Ledger

| Keep | Cut | Defer | Question |
| --- | --- | --- | --- |
| ... | ... | ... | ... |
```

Lead with the rewritten plan, not a long critique. Keep explanation short and concrete.

## Guidelines

- Be ruthless but not reckless.
- Preserve safety, correctness, data integrity, and a real verification path.
- Prefer one vertical slice over broad horizontal infrastructure.
- Prefer manual or existing workflows over new automation for the first slice.
- Treat "we might need it later" as a reason to defer, not a reason to keep.
- Do not turn this into a strategy review, brainstorming session, or architecture redesign.
- Do not invent extra acceptance criteria while trimming.
