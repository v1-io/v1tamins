---
name: v1-designing-habit-systems
description: Use when designing a habit, routine, or cadence that sticks for a person, team, or process, or when an existing one keeps failing. Triggers on "help me build a habit", "make this schedule stick", "design a routine", "why do we keep falling off", "habit system", "standing cadence that sticks".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---
# Designing Habit Systems

Design recurring-behavior systems from the primary research instead of folklore. Scope can be an individual, a team, or a process cadence. Every output element must cite a numbered research pillar in [references/research.md](references/research.md); read it before designing.

## Choose mode

| Mode | Use when | Flow |
| --- | --- | --- |
| **Design** | Building a new habit, routine, cadence, or schedule | Shared intake → anchor inventory → design behaviors → launch/cadence → output spec |
| **Diagnosis** | An existing system keeps failing | Shared intake → failure-mode table → targeted cures (skip anchor inventory and full spec unless a cure requires them) |

## Quick Start

**Design:** intake → anchor inventory → design each behavior → launch/cadence → emit spec table.

**Diagnosis:** intake → map decayed elements to failure modes → prescribe cures from the failure-mode table.

## Shared intake

Establish before designing or diagnosing:

- Target behaviors, concretely ("range practice 2x/week", "incident review every Monday", not "get better at golf" / "improve ops hygiene").
- Actors and fixed constraints: work hours, on-call, family duties, chronotype, deadlines, timezone spread. Do not design against a constraint already declared immovable (a night-owl individual gets evening slots; an async-heavy team does not get a mandatory 6am standup).
- Past failures: what systems were tried and how they decayed. In **Design** mode, each past failure must map to a named failure mode in Diagnosis mode — the new design must address it explicitly.
- Available data sources: calendars, tickets, wearables, transactions, receipts, CI/deploy logs. Prefer designs whose adherence is observable without self-report.

## Design mode

### Anchor inventory

List existing daily/weekly fixed events for the relevant actors. Rank each anchor on four properties; best anchors have all four:

1. Happens daily (or on every target day).
2. Externally enforced (a child's bedtime, a school run, a standing customer call, a deploy window — not self-discipline alone).
3. Same place every time (physical or consistent channel/tool).
4. Same preceding event every time.

Reject clock-time anchors ("at 7pm") when an event anchor exists ("when the baby is down", "when the weekly deploy finishes"). Reject fuzzy anchors ("in the evening", "after dinner", "sometime Friday") outright.

### Design each behavior

For every target behavior, fill every column in the output table:

- **If-then** (required): bound to a ranked anchor — "When [anchor event], [actor] [specific action] at [place/channel]." Cite pillar 1.
- **Friction moves** (required): at least one step removed from the good path (gear pre-staged, template pre-filled, order pre-placed) or added to the bad path (app off home screen, merge blocked without checklist). Cite pillar 2 or 7.
- **Commitment device** (required when stakes matter; otherwise `—` with one-line rationale): booked slot, prepaid session, filled cart, named owner with public commitment, calendar hold with attendees. A solo calendar block alone is not a commitment device. Cite pillar 6 when present.
- **Temptation bundle** (required when the behavior is aversive; otherwise `—` with one-line rationale): a specific pleasure or valued side-benefit reserved exclusively for it. Cite pillar 4 when present.
- **Adherence signal** (required): how completion is detected automatically (GPS activity, receipt, ticket state, attendance log, deploy record). Allow at most one self-reported metric per system. Cite pillar 8 when review-based; otherwise note the observable source.

### Launch and cadence

- Set the launch on a temporal landmark (Monday, the 1st, post-trip return, post-release) — never "starting today" mid-cycle without cause. Cite pillar 5.
- State the expectation explicitly in the output: ~10 weeks to automaticity (median 66 days); effort in weeks 1–8 is normal, not failure. Cite pillar 3.
- Miss rules, verbatim in the output: one miss is noise, do nothing; two consecutive misses is a design defect — redesign that element, never prescribe "try harder". Cite pillar 3.
- Schedule a weekly review against objective data. Reviews beat reminders: assume push nudges will be habituated away and ignored. Cite pillar 8.
- Any planned disruption (trip, holiday, launch crunch, org change) gets a written re-entry plan dated before the disruption starts, because disruptions break good habits as effectively as bad ones. Cite pillar 5.

## Diagnosis mode

When the request is "why does this system keep failing", map each decayed element to a failure mode and prescribe its cure:

| Failure mode | Symptom | Cure |
| --- | --- | --- |
| Floating to-do | Behavior scheduled with no anchor event | Bind to a ranked anchor (Design mode) |
| Willpower start | First step requires in-the-moment motivation | Pre-stage; move decision to the night/week before |
| Chronotype fight | Slot contradicts the actors' energy or availability pattern | Relocate the slot; keep the behavior |
| No stakes | Only a calendar block, nothing booked, owned, or paid | Add a commitment device (pillar 6) |
| Nudge habituation | Reminders fire but are ignored | Replace pings with a weekly data review (pillar 8) |
| Double-miss spiral | One lapse read as failure, system abandoned | Install the miss rules from Design mode launch/cadence |
| Disruption collapse | System died after a trip, crunch, or context change | Re-launch on a landmark with a re-entry plan (pillar 5) |

If a cure requires redesign, apply only the relevant Design-mode steps — do not run the full design workflow unless the user asks for a new system.

## Output

**Design mode** — emit a habit system spec:

| Behavior | Anchor (rank) | If-then | Friction moves | Commitment device | Bundle | Adherence signal |
| --- | --- | --- | --- | --- | --- | --- |

Followed by: launch date (landmark), miss rules, review cadence, re-entry plan trigger, and — per element — the research pillar that justifies it. Drop any element that cannot name its pillar.

**Diagnosis mode** — emit a failure-mode table with one row per decayed element: symptom, named failure mode, cure, and pillar citation. Offer to switch to Design mode if the cures imply a full rebuild.

## Chaining

- Use `v1-interview-me` first when the behavior goal is still vague and needs office-hours questioning before design.
- Use `v1-diagnosing-constraints` when the stuck system is a throughput problem (queue, funnel, WIP, bottleneck) — not a recurring behavior that fails to stick.
- Use `v1-debug` when the failure is a general expected-versus-actual gap that is not habit, routine, or cadence decay.
- Use `v1-deep-research` when the user wants a literature survey without system design.

## When Not To Use

- Do not use for throughput, WIP, or queue bottlenecks; use `v1-diagnosing-constraints`.
- Do not use for general expected-versus-actual failures that are not habit, routine, or cadence failures; use `v1-debug`.
- Do not use for general idea fleshing before the recurring behavior is defined; use `v1-interview-me`.
- Do not use for multi-source research without habit/routine system design; use `v1-deep-research`.

## Reference Files

- **[references/research.md](references/research.md)** — eight numbered research pillars with verified citations and effect sizes; the evidence base every design element must trace to.
