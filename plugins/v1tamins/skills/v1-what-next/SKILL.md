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

Name the one next thing to do.

Start from this thread. Look outside it only when the thread has no clear next
move. If neither the thread nor the project shows one, say so. Don't guess.

If they want a v1 skill, not a next step, use `v1-menu`. If what's needed is a
plan, point at a planning skill instead of writing the plan here.

## Workflow

### 1. Reorient

From the thread, name the original goal in one sentence, what's been verified
as done, and the open loops: unanswered questions, steps that were proposed
but never taken, errors seen and not resolved. Leave decisions the user already
made alone.

Run `git status` only when the next step depends on whether work is committed
and the thread doesn't already say. Don't follow task, plan, or issue links
yet. If the answer hinges on one, put that under "Needs you".

### 2. Look outward when the thread runs dry

If the goal is done, or nothing left in the thread ranks above "everything
else", find where this project keeps follow-up work before you answer. Don't
assume a particular tool. Look in this order:

- Whatever the thread named as the owner of the work: a ticket, plan, or task
  it started from.
- The project's instructions or contributor docs, which usually say where work
  is tracked.
- What the repo or workspace actually has: an issue list, a plans or tasks
  directory, a roadmap, a TODO file, open review requests.

Read only enough to find the item closest to what just happened: same area,
same goal, or a follow-up the finished work created. Stop at the first source
that gives you candidates. Mark anything found this way as outside the thread
so the user knows where it came from. If nothing turns up, say that and offer
the smallest wrap-up that won't get lost.

### 3. Rank

Pick the next move in this order:

1. Finishes or unblocks the original goal.
2. Verifies something currently claimed but unproven.
3. Prevents loss: uncommitted work, an unrecorded decision, an answer that
   would be expensive to reconstruct later.
4. Everything else, including follow-ups and related work found outside the
   thread.

Do the smallest thing that moves the top item. If that item is waiting on a
user decision, the next move is that decision, asked simply, with a default.
If the last response left several questions, name the one that actually
blocks and default the rest.

### 4. Answer

```markdown
**Next:** [one concrete action, one sentence]

**Why:** [one or two sentences tying it to the goal and state; mark anything
unverified]

**Also on the table:** [only when a runner-up is a genuinely close call]

**Needs you:** [only when a decision blocks the next step: the question and
a default]
```

Don't offer a menu of equals. When the work is done, say so, and say whether
to stop, commit, or hand it off.

## Example

The last response ended with four questions about naming, file layout, test
scope, and rollout. Answer: "Next: confirm the file layout. I default to option
A for naming and skip rollout for now; the other questions do not block
implementation."
