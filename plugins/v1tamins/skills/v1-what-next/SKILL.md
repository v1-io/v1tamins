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

Recommend the next useful action based on what is true now.

Use the thread to understand the goal and check whether things have changed.
Default to finishing that goal; if the user asks for project priorities or options, use
that scope instead. If neither the thread nor the project shows a useful next
move, say so. Recommend the action; do not start implementation, change files,
update a tracker, or contact anyone from this skill.

If they want a v1 skill, not a next step, use `v1-menu`. If what's needed is a
plan, point at a planning skill instead of writing the plan here.

## Workflow

### 1. Find where things stand

From the thread, name the original goal in one sentence, what's been verified
as done, and what remains: unanswered questions, steps that were proposed
but never taken, errors seen and not resolved. Leave decisions the user already
made alone.

Before recommending an action, check the fact that makes it necessary when
another session, release, scheduled run, or person could have changed it.
Use the smallest read-only check with the tools permitted here: the installed
version, current task or PR status, run result, or `git status` when a commit
is at issue. Reuse evidence already checked in this turn. Before advising
someone to wait, check the current time and whether the expected event ran.
Use the record where this work is tracked unless it is outdated, conflicts
with other evidence, or leaves the question unanswered.

Do quick read-only checks yourself before recommending the next task. Check
available sources before asking someone for material they may already contain. Stop when you have enough information to choose; don't
turn this into a full audit or perform a substantial investigation. Recommend
that investigation if it is the next useful action. If access is unavailable,
say what you could not check and how to get it. A missing fact is not a
choice for the user to make.

### 2. Look beyond the thread when needed

If the user asks for project priorities, the goal is done, or nothing left in
the thread ranks above "everything else", find where this project keeps work
before you answer. Otherwise stay with the thread's goal. Don't assume a
particular tool. Look in this order:

- Whatever the thread named as the owner of the work: a ticket, plan, or task
  it started from.
- The project's instructions or contributor docs, which usually say where work
  is tracked.
- What the repo or workspace actually has: an issue list, a plans or tasks
  directory, a roadmap, a TODO file, open review requests.

Use the first relevant source of tasks. Compare what each would achieve, how
urgent it is, what it needs first, and who can do it. For thread follow-ups, start
with the same goal or area; for project priorities, favor what matters most over
what resembles the last task. Check that the chosen task still needs doing.
Mark recommendations found outside the thread and name their source.
If nothing useful turns up, say so; don't invent housekeeping to keep busy.

### 3. Choose the next move

Pick the next move in this order:

1. Finishes or unblocks the goal in the requested scope.
2. Verifies something currently claimed but unproven.
3. Prevents loss: uncommitted work, an unrecorded decision, an answer that
   would be expensive to reconstruct later.
4. Everything else, including follow-ups and related work found outside the
   thread.

Recommend the smallest useful action on the top item and name who can take
it. Distinguish required human approval from work an agent can do afterward;
this skill's read-only boundary does not make every next action human-only.
If it is waiting on another person or a future event, say what it needs first
and consider independent work that advances the same goal. If none exists,
say to wait or stop; don't imply that monitoring has been scheduled.

If a user decision blocks progress, present the evidence, your recommendation,
and what they would give up or what is still unproven. Don't just ask them to
review a task list. Carry forward prior approvals within their scope. If the last
response left several questions, ask only the one that blocks and state
reasonable defaults for the rest; a default is not permission to act.

### 4. Answer

Write for someone who knows the project but has not followed every turn.
Name the work and explain why it matters before giving task IDs or file paths.
Use everyday words; explain technical terms only when they help the decision.
Keep uncertainty, conditions, and the difference between proposed and done.
Keep claims no stronger than the evidence: a partly successful check does not
prove the fix works. Add no facts, owners, deadlines, or commitments to make
the answer sound complete. Clearly label any suggested owner or next step.
Link supporting detail, but put enough explanation in the answer to act on it.

Use the shape below when helpful. A simple answer can be a short paragraph;
leave out empty sections, repeated summaries, and automatic offers to help.
Before replying, check: can the reader tell what to do, why now, and whether
anything needs their input? Cut repetition, not the explanation they need.

```markdown
**Next:** [one concrete action and who can take it, one sentence]

**Why:** [explain why this matters now and what, if anything, is still unknown]

**Also on the table:** [only when a runner-up is a genuinely close call]

**Needs you:** [only when human input or access is required: the specific
request; for a decision, include your default and its tradeoff]
```

Give one recommendation by default. If the user explicitly asks for options,
give the requested number when evidence supports them, rank them, and mark
your pick. Don't pad a list with invented work. When the work is done, say so,
and say whether to stop, commit, or hand it off.

## Examples

The last response ended with four questions about naming, file layout, test
scope, and rollout. Answer: "Next: confirm the file layout. I default to option
A for naming and skip rollout for now; the other questions do not block
implementation."

An older turn says a release is waiting on a scheduled run. The current
run result shows it passed on the installed version. Don't recommend waiting or
checking that result again. Report that the check passed, then recommend
the remaining action or say the goal is complete.

A task still says "review the PR," but the fix is installed and the scheduled
run passed. Both requirements are met; an optional export was deferred. Answer:
"The fix is installed and today's scheduled run passed. I recommend closing
this task. The optional export can stay separate. If you agree, an agent can
update the task after your approval."
