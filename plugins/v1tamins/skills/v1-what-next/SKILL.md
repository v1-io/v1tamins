---
name: v1-what-next
description: Use when deciding what to work on next from the current thread or the surrounding project. Triggers on "what next", "what should we do next", or "where were we".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---
# What Next

Read the current thread and propose the single best next thing to work on. This
is a lightweight checkpoint: it proposes, and the user decides. If the user says
"continue" or "do the next step", do the work instead of running this skill.

Start from the thread. Look outside it only when the thread alone gives no
clear next move. Never guess: if neither the thread nor the project shows a
next step, say so. If the question is which v1 skill fits rather than which
work comes next, use `v1-menu`. If the honest answer needs a plan, recommend a
planning skill rather than writing the plan here.

## Workflow

### 1. Reorient

From the thread, establish the original goal in one sentence, what is verified
done, and the open loops: unanswered questions, proposed steps never taken,
errors seen but not resolved. Do not reopen decisions the user already made.

Run `git status` only when the recommendation depends on whether work is
committed and the thread does not already say. Do not chase references the
thread makes to tasks, plans, or issues at this stage; if the answer hinges on
one, say so under "Needs you".

### 2. Look outward when the thread runs dry

If the goal is complete, or nothing in the thread ranks above "everything
else" in the next step, find where this project's follow-up work lives before
answering. Do not assume a particular tool. Look, in order, for:

- The place the thread itself named as the owner of the work: a ticket, plan,
  or task it was started from.
- The project's instructions or contributor docs, which usually say where work
  is tracked.
- Whatever the repository or workspace exposes: an issue list, a plans or
  tasks directory, a roadmap, a TODO file, open review requests.

Read only enough to find the item most connected to what was just done: same
area, same goal, or a follow-up the finished work created. Stop after the first
source that yields candidates. Mark anything found this way as outside the
thread so the user knows its provenance. If no source exists or none yields a
related item, say that plainly and offer the smallest durable wrap-up instead.

### 3. Rank

Pick the next move by this priority:

1. Finishes or unblocks the original goal.
2. Verifies something currently claimed but unproven.
3. Prevents loss: uncommitted work, an unrecorded decision, an answer that
   would be expensive to reconstruct later.
4. Everything else, including follow-ups and related work found outside the
   thread.

Prefer the smallest move that advances the top-ranked item. If the top-ranked
item is blocked on a user decision, the next move is that decision, stated in
its simplest form with a default. When the previous response left several
questions, name the one that actually blocks and default the rest.

### 4. Answer

```markdown
**Next:** [one concrete action, one sentence]

**Why:** [one or two sentences tying it to the goal and state; mark anything
unverified]

**Also on the table:** [only when a runner-up is a genuinely close call]

**Needs you:** [only when a decision blocks the next step: the question and
a default]
```

Never offer a menu of equals. Say plainly when the workstream is complete and
the right move is to stop, commit, or hand off.

## Example

The last response ended with four questions about naming, file layout, test
scope, and rollout. Answer: "Next: confirm the file layout. I default to option
A for naming and skip rollout for now; the other questions do not block
implementation."
