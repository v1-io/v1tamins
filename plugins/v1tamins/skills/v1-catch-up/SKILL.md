---
name: v1-catch-up
description: Summarize what changed since the user's last message in under 150 words, with a compact visual and human-only decisions. Triggers on "catch me up" or "what happened".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---
# Catch Up

Answer the backward-looking question: “What actually changed since my last
message, and what needs my eyes?” Stay within the current session. If the user
wants the highest-leverage next move in the thread or project, point to
`v1-what-next`.

Use this skill to inspect and report. Keep tools read-only. Leave files,
trackers, messages, and jobs as they are. Read existing peer results without
launching new work.

## 1. Gather

Start at the previous message authored by the user, before the catch-up
request. Notifications, subagent results, and tool output never reset that
boundary. If the earlier conversation is unavailable, state the coverage gap.

- Collect requested outcomes, completed work, peer results, and relevant
  messages since that boundary. Carry forward earlier human requests that
  still block the work. Drop resolved requests.
- Verify the current state of every touched pull request, CI run, or background
  job. Read its live owner with any available read-only tool or CLI. Check
  numbers against their source. Mark anything you cannot confirm `unchecked`
  and name the gap briefly. A notification or prior result can go stale.
- Identify work only the user can unblock, such as a product decision, an
  approval, an irreversible step reserved for them, or missing access they must
  grant. Keep agent-solvable checks and repairs out of this list. Include an
  item only when the evidence shows it still needs the user.

## 2. Write

Use fewer than 150 words total. Count words in labels, captions, alt text,
and visuals, including visible screenshot text. Use plain words and short
sentences. Say “tests pass.” Keep identifiers, paths, and counts only when the
user needs them to act. State each fact once across text and visuals. Omit
routine work that changed nothing for the user.

1. Open with one line stating how many things need the user, or say “Nothing
   needs you.” If nothing changed, nothing is pending, and the evidence covers
   the interval, say so on that line and stop.
2. Show one compact visual with each requested outcome and any bug found and
   fixed along the way. Use a status strip, a small Mermaid state or flow
   diagram, or an existing session screenshot when a UI changed and the image
   makes the outcomes and their statuses clear. Use a text strip when no
   suitable screenshot is available or diagrams cannot render. Skip tables.
   - Use up to six plain-spoken boxes with at most eight words each. Group
     related outcomes as needed. Use fewer boxes for a small update.
   - Mark each outcome `done`, `running`, `failed`, or `unchecked`. Use
     `done` for confirmed results, `running` for verified work in progress,
     `failed` for a confirmed failure, and `unchecked` when evidence is missing.
   - For a choice between options, include a compact tradeoff or before/after
     row in the same visual. Label the choices with what changes for the user.
3. Give each human-only item two short lines. On the first, recommend a choice
   or action and explain why. Include any prerequisite or irreversible effect.
   On the second, say what happens if it goes unanswered. Write “unknown” for
   any consequence you cannot establish. Number items only when there are
   several. Leave this part out when nothing needs the user.

Before sending, count the words and trim process detail until the reply fits.
Keep every unresolved human decision and every requested outcome visible.

## Examples

**Active handoff.** One peer finished an export and another fixed a bug that
skipped blank rows. The live test run is still going. The product owner still
needs to choose the default export format.

> One decision needs you.
>
> ```text
> [Export done] [Blank rows fixed] [Tests running]
> [CSV: opens in spreadsheets] [JSON: preserves nested fields]
> ```
>
> Make CSV the default because most users open exports by hand.\
> If unanswered, the default stays unset and release waits.

**Quiet completion.** A status read confirms the requested fix and test run
both finished. No one is waiting for a decision.

> Nothing needs you.
>
> `[Date filter fixed · done] [Tests pass · done]`
