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

Recommend the highest-leverage next move based on what is true now.

Stay read-only from this skill: recommend the move without starting
implementation, editing files, updating a tracker, or contacting anyone. If the
user chains an authorized request with this skill (for example, "close the
ticket, then what-next"), complete the explicitly requested action first, then
run this read-only checkpoint on the resulting state.

If they want a v1 skill rather than a next step, point to `v1-menu`.
If they only want to know what changed since their last message, use `v1-catch-up`.
If what is needed is a plan, point to a planning skill instead of writing the plan here.

## Workflow

### 1. Pick the mode and constraints

Read the thread for the original goal, what is verified done, what remains, and
decisions the user already made (leave settled decisions alone). Choose the
mode that fits:

| Mode | When | Target shape |
| --- | --- | --- |
| **Cold single-track** (default) | First checkpoint on one active goal | Concise brief (~80–150 words) |
| **In-session repeat** | Already checkpointed this thread ("sent, what next?") | 1-line delta of what cleared + new move (~50–100 words); do not re-explain the unchanged goal |
| **Multi-track** | Parallel PRs, active subagents, or multiple deliverables | Compact status board + numbered steering handles |
| **Project priorities** | User asks for project priorities/options, or thread goal is done | Scan external work sources, rank by impact, mark external sources |

Honor any stated constraint without adding ceremony when none is given:
- **Short window** ("I have 10 minutes"): favor a quick win or starting a slow external/async clock before leaving.
- **Stepping away / overnight**: favor safe autonomous agent work to kick off now, or clean state-saving before stopping.
- **Stuck / spinning**: apply the zoom-out check aggressively to challenge the premise or cut scope.

### 2. Verify live state

Before recommending an action, check the live owner of the deciding fact when
another session, release, scheduled run, or person could have changed it. Use
the smallest read-only check with any available read-only tool or authorized
CLI: git/PR/CI state, messages or comments, installed version, run result, or
running tasks. Do not rely on the thread or a tracker mirror alone when a live
source can confirm whether the blocker still exists.

Reuse evidence already checked in this turn. Before advising someone to wait,
check the current time and whether the expected event ran. Stop once you have
enough to choose; do not turn this into a full audit — recommend that
investigation if it is the next useful move. If access is unavailable, name
what you could not check and how to get it; a missing fact is not a choice for
the user to make.

### 3. Look beyond the thread when needed

If the user asks for project priorities, the goal is done, or nothing left in
the thread warrants action, find where this project keeps work before
answering. Otherwise stay with the thread's goal. Do not assume a particular
tool. Look in this order:

1. Whatever the thread named as the owner of the work: a ticket, plan, or task.
2. Project instructions or contributor docs naming the tracker.
3. What the repo or workspace holds: open issues, PRs, plans/tasks folders, roadmap, or TODOs.

Stop at the first relevant source. Compare impact, urgency, lead time, and who
can act. For thread follow-ups, start with the same goal or area; for project
priorities, favor what matters most over what resembles the last task. Verify
the chosen item still needs doing, mark it as outside the thread, and name its
source. If nothing useful turns up, say so — never invent busywork.

### 4. Choose the highest-leverage move

Run a silent **zoom-out check** before accepting the obvious next step. Speak up
only when one genuinely applies:
- **Shortcut:** Can one move solve multiple open items, or has a planned step become obsolete?
- **Blind spot:** Is the next step relying on unproven work, a stale premise, or an unstated identity/account choice?
- **Finish line:** Is the goal already met with only optional polish left (say to stop and close/ship), or is a last-mile step missing (uncommitted diff, unmerged PR, stale tracker, uninstalled build)?

Rank candidate moves in this order:

1. **Unblocks or finishes the goal** — *with a verification gate:* before any external, irreversible, or high-stakes step (sending outside, merging, releasing, closing), if the underlying work is claimed but unproven, **verifying or reviewing it becomes #1**.
2. **Prevents loss** — uncommitted work, unrecorded decisions, or unfinished last-mile delivery steps.
3. **Highest-leverage remaining work** — including follow-ups and external priorities.

Sequence across the three clocks (human attention, agent compute, external wait):
- **Start slow clocks early:** If a quick human ping or async run starts a long external wait (teammate reply, CI, review) that unblocks downstream work, surface it first.
- **Shrink human homework first:** Before assigning raw review or triage to the user, check if an agent can reduce it to a small decision first (classify unknowns, draft a shortlist, run a check) and recommend that agent prep step first.
- **Pair human/waiting moves with parallel agent work:** Whenever `#1` waits on the user, another person, or a future event, explicitly name the best unblocked agent move that can run right now alongside it. If none exists, say to wait or stop without implying monitoring was scheduled.
- **Batch ripe human decisions:** When multiple small decisions block progress, group them as numbered items (`1, 2, 3`), each with a recommendation and default, so the user can steer in one line. If an earlier turn left several questions and only one blocks, ask only the blocker and state defaults for the rest (a default is not permission to act).
- **Take a stand:** Never open `**Next:**` with `"You decide whether..."`. State your recommended choice, what is given up or unproven, and—only when open or risky—the execution detail that matters (draft vs. send, which account acts, edit in place vs. new copy). Carry forward prior approvals within their scope.

### 5. Answer

Write for someone who knows the project but has not followed every turn. Aim
for **80–150 words** by default (**50–100** for a repeat delta; up to **180**
for a multi-track board with an inline draft). State each fact once.

- **Concrete plain-language test:** Say what actually changes (and unpack internal labels or vague references like "the package") in everyday words before task IDs or file paths.
- **Truthful evidence:** Briefly name what you checked or could not check. Keep claims no stronger than the evidence (a partial check does not prove a fix works), keep uncertainty explicit, and invent no facts, owners, or deadlines.
- **Spatial orientation (conditional):** Only on 3+ step arcs or 2+ parallel tracks, include a 1–3 line progress strip (`[✓] ... → [▶] ... → [ ] ...`) or 3-lane board (**Agent now / Needs you / In flight**). Skip it on simple 1-step answers.
- **Ready-to-act handoff (no extra headings):**
  - Short human message/ping needed? Put a ready-to-paste 2–3 line draft directly under that item.
  - Agent can execute next? Close with one plain sentence naming exact scope and stop point so `"go"` works (never add a separate contract heading or bulleted spec).
  - A packaged skill clearly owns the next step (especially explicit-only skills like `/v1-land-pr`, `/v1-review-board`, `/v1-implement-unit`, `/v1-prove-work`, or `/v1-debug`)? Name it.
  - Number items (`1, 2`) only when presenting multiple parallel moves or decisions, and reference only numbers you actually wrote.
- **Session hygiene:** When this thread's goal is complete and the best next move belongs to a different area, say this thread is done (note any last-mile close-out) and give a ready-to-paste 2–3 line starter prompt for a fresh session.

Use the shape below when helpful. Drop empty sections—never include a section
just to dismiss an unrelated item, never repeat `**Next:**` inside
`**Needs you:**`, and skip automatic offers to help. Give one pick by default;
if the user asks for options, give up to the requested number supported by
evidence, ranked, with your pick marked.

```markdown
**Next:** [one concrete action, who takes it, and the recommendation — one sentence]

**Why:** [the deciding leverage: what it unblocks, what clock/risk it addresses, and what was checked or remains unknown]

**Also on the table:** [omit unless there is a genuine close call OR an unblocked parallel agent move]

**Needs you:** [omit if already covered in Next or if nothing requires human input/access]
```

## Examples

**Collapsing multiple questions:** The last turn ended with four questions on naming, file layout, test scope, and rollout. Answer: *"Next: confirm the file layout (recommended: split by domain — keeps tests isolated at the cost of two extra imports). I default to option A for naming and skip rollout for now; neither blocks implementation. Say 'go' to implement with those defaults."*

**Unverified work before an external send:** A client email draft is due today, but the underlying numbers have not been reviewed yet. Do not recommend sending the email first. Answer: *"Next: have an agent review the draft calculations before you send the email. Why: the email is due today, but the latest revision is unverified — sending now risks client-facing errors. Say 'go' and I will review both sheets and report any discrepancies before you send."*

**Repeat-turn multi-track checkpoint:** The user says *"sent that email. /v1-what-next"* in a session with an open PR stack and an urgent contract typo. Answer with a 1-line delta, a compact strip, and two numbered items: **(1)** the time-sensitive human ping with a ready-to-paste 2-line message, and **(2)** the parallel agent move on the PR stack with a one-sentence scope/stop cue so the user can reply `"go on 2"`.

**Stale tracker, finished goal, and fresh-session handoff:** The ticket still says *"review the PR"*, but live checks confirm the fix is merged, installed, and today's scheduled run passed (`exit 0`). Answer: *"This goal is done — I checked the installed build and today's run passed. Last-mile check: tree is clean; say 'close it' and I will close the ticket (keeping the deferred export separate). Next project priority (from open issues): webhook retry timeouts (#412). Start a fresh session with: `Investigate #412 webhook retry timeouts in worker/hooks.py; read the last 3 failure logs first, then propose the smallest fix.`"*
