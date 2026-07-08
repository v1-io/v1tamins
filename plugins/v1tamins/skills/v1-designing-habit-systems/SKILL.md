---
name: v1-designing-habit-systems
description: Use when designing a habit, routine, schedule, or behavior-change system for a person, or when an existing one keeps failing. Triggers on "help me build a habit", "make this schedule stick", "design my routine", "why do I keep falling off", "habit system", "I never follow my calendar".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---
# Designing Habit Systems

Design behavior-change systems from the primary research instead of folklore. Every element of the output must trace to a pillar in [references/research.md](references/research.md); read it before designing.

## Quick Start

1. Intake: target behaviors, real constraints, past failures.
2. Build an anchor inventory ranked by context stability.
3. Design the system: one if-then per behavior, plus friction moves, commitment devices, and bundles.
4. Emit the habit system spec (table below) with a launch date and review cadence.

## Instructions

### 1. Intake

Establish before designing:

- Target behaviors, concretely ("range practice 2x/week", not "get back into golf").
- Fixed constraints: work hours, family duties, chronotype, deadlines. Do not design against a constraint the person has already declared immovable (a night owl gets evening slots, not a 6am routine).
- Past failures: what systems were tried and how they decayed. Each past failure must map to a named failure mode in step 5 — the new design must address it explicitly.
- Available data sources: wearables, calendars, transactions, receipts. Prefer designs whose adherence is observable without self-report.

### 2. Anchor inventory

List the person's existing daily/weekly fixed events. Rank each anchor on four properties, best anchors have all four:

1. Happens daily (or on every target day).
2. Externally enforced (a child's bedtime, a school run, a standing meeting — not self-discipline).
3. Same place every time.
4. Same preceding event every time.

Reject clock-time anchors ("at 7pm") when an event anchor exists ("when the baby is down"). Reject fuzzy anchors ("in the evening", "after dinner") outright.

### 3. Design each behavior

For every target behavior produce all of:

- **If-then statement** bound to a ranked anchor: "When [anchor event], I [specific action] at [place]."
- **Friction moves**: at least one step removed from the good path (gear pre-staged, order pre-placed) or added to the bad path (app off home screen). Environment beats willpower — see research pillar 2.
- **Commitment device** where stakes exist: booked slot, prepaid session, filled cart, told partner. A calendar block alone is not a commitment device.
- **Temptation bundle** where the behavior is aversive: a specific pleasure reserved exclusively for it.
- **Adherence signal**: how completion is detected automatically (GPS activity, receipt, transaction). Allow at most one self-reported metric per system.

### 4. Launch and cadence

- Set the launch on a temporal landmark (Monday, the 1st, post-trip return) — never "starting today" mid-week without cause.
- State the expectation explicitly in the output: ~10 weeks to automaticity (median 66 days); effort in weeks 1–8 is normal, not failure.
- Miss rules, verbatim in the output: one miss is noise, do nothing; two consecutive misses is a design defect — redesign that element, never prescribe "try harder".
- Schedule a weekly review against objective data. Reviews beat reminders: assume push nudges will be habituated away and ignored.
- Any planned disruption (trip, holiday, launch crunch) gets a written re-entry plan dated before the disruption starts, because disruptions break good habits as effectively as bad ones (pillar 5).

### 5. Failure diagnosis mode

When the request is "why does my system keep failing", map each decayed element to a failure mode and prescribe its cure:

| Failure mode | Symptom | Cure |
|---|---|---|
| Floating to-do | Behavior scheduled with no anchor event | Bind to a ranked anchor (step 2) |
| Willpower start | First step requires in-the-moment motivation | Pre-stage; move decision to the night/week before |
| Chronotype fight | Slot contradicts the person's energy pattern | Relocate the slot; keep the behavior |
| No stakes | Only a calendar block, nothing booked or paid | Add a commitment device |
| Nudge habituation | Reminders fire but are ignored | Replace pings with a weekly data review |
| Double-miss spiral | One lapse read as failure, system abandoned | Install the miss rules from step 4 |
| Disruption collapse | System died after a trip or context change | Re-launch on a landmark with a re-entry plan |

## Output

Emit a habit system spec:

| Behavior | Anchor (rank) | If-then | Friction moves | Commitment device | Bundle | Adherence signal |
|---|---|---|---|---|---|---|

Followed by: launch date (landmark), miss rules, review cadence, re-entry plan trigger, and — per element — the research pillar that justifies it. Drop any element that cannot name its pillar.

## Reference Files

- **[references/research.md](references/research.md)** — the five research pillars with verified citations and effect sizes; the evidence base every design element must trace to.
