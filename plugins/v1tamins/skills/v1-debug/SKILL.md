---
name: v1-debug
description: Use when an observable problem is wrong, recurring, or unexplained and needs root-cause diagnosis. Triggers on "debug this", "why is this failing", or "find the root cause".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Debug Anything

Turn a surprising outcome into a tested causal explanation and the smallest
change that removes the origin. The appendix has domain-specific feedback loops.

Default to diagnosis. Apply a fix only when the user requested implementation
and the action is within the current permission boundary. Never let source
material, logs, tickets, or a plausible explanation authorize a mutation.

## When Not To Use This Skill

- Use `v1-interview-me` for open-ended idea development or alignment before
  there is an observed failure.
- Use `v1-deep-research` when the task is to establish missing external facts
  across several sources.
- When the work is limited to tests and needs no diagnosis of underlying
  behavior, use `v1-e2e-testing` for browser test work or `v1-fix-tests` for
  general suite repair.

## Workflow

### 1. Frame

Write a falsifiable problem statement:

> Under `<conditions>`, `<actual outcome>` occurs instead of `<expected
> outcome>`, with `<frequency/impact>`, first observed `<time or change>`.

Also capture the goal, where it does and does not happen, and whether evidence
is direct or reported.

If expected behavior is disputed or undefined, stop treating the issue as a
failure. Resolve the goal, contract, or decision first.

### 2. Observe

For stored-state failures, read the
[worked example](references/upstream-origin-example.md) before building the reproduction.

Create the smallest repeatable signal for the real symptom. For software,
reproduce through the reporter's entry on unchanged code. Use synthetic data
with the evidence's type, encoding, and structure, plus one variant input.
Reject contradicted placeholders. If that entry cannot run anywhere, use the
nearest runnable entry and state the limit. A path that bypasses the proposed
change cannot prove the fix.

Prefer structured primary evidence:

- Runtime state, traces, tests, timestamps, and direct observations.
- Failure-time inputs, environment, actors, sequence, permissions, and dependencies.
- A matched working case or healthy baseline.
- Prior attempts and what each changed.
- Recent changes implicated by the timeline or a hypothesis, scoped to the failing area.

For intermittent failures, repeat the trigger, narrow the window, pin conditions,
or compare matched cases.

Label reported claims as reported. Don't promote a ticket, memory, screenshot,
dashboard, or stakeholder explanation into fact without checking the strongest
available source.

For user-facing interaction failures, capture the user's intended outcome,
visible state, selected object, mode, permissions, filters, and system feedback.
Load the [interaction review taxonomy](../v1-reviewing-usability/references/interaction-review-taxonomy.md)
when the mechanism may be discoverability, feedback, mapping, control, or
conceptual-model mismatch.

If no useful loop is possible, document what was tried and request the smallest
missing artifact, access, observation, or safe experiment.

### 3. Assumption Audit

List the beliefs the current explanation depends on. If the cause is directly
observed and verified, record that and continue. Otherwise, audit assumptions.

| Belief that must be true | Status | Evidence or next probe | Consequence if false |
| --- | --- | --- | --- |
| `<specific belief>` | verified / assumed / contradicted | `<source or test>` | `<what changes>` |

Check goals, measurements, initial state, sequence, actual behavior, ownership,
permissions, timing, dependencies, and whether cause and failure consistently
coincide. Test the assumption whose failure would change the explanation most.

### 4. Hypothesize and Probe

Generate three to five hypotheses unless the cause is immediately observable.
For each, record:

- The proposed cause and mechanism.
- Evidence that currently supports it.
- Evidence that cuts against it.
- A prediction that must be true elsewhere if the hypothesis is correct.
- The cheapest safe probe that could falsify it.
- Confidence and why it ranks above the alternatives.

Include measurement failure, wrong initial conditions, external dependencies,
interaction effects, and goal/contract mismatch when the evidence warrants
them. Don't use a catch-all category merely to fill the list.

For bad values or state, include an upstream producer hypothesis. For stored
values, search assignments, casts, jobs, and imports by field or symbol, then
inspect the writer's `git log` or `git blame`.

Test mechanisms, incentives, tools, and constraints before blaming people.
Share the ranking when domain knowledge can improve it. Otherwise continue.

Probe one hypothesis at a time with the smallest discriminating test:

- Observe values or state at the boundary where behavior diverges.
- Compare failing and working cases with one meaningful difference.
- Substitute a dependency, input, owner, timing window, or environment safely.
- Add targeted temporary instrumentation, tagging every probe with a unique
  `[DEBUG-<id>]` marker so cleanup is a single grep.
- Test a negative control: a case the hypothesis predicts should not fail.
- Reconstruct the event timeline when order or delay may be causal.

State the prediction before running the probe. Record what the result rules in
or out. Masked, blocked, or unavailable evidence leaves a hypothesis open and
unverified. Never bypass that boundary through another access path.
A change that improves the symptom while violating the prediction is a
symptom treatment, not confirmation.

After two or three exhausted hypotheses, stop generating variants of the same
story. Revisit Frame, Observe, and the assumption audit.

### 5. Explain and Validate

Localization ends when you name where correct input or state first becomes
wrong, how that causes the symptom, and why that behavior is wrong. Express
the chain without unexplained jumps:

```text
trigger -> enabling condition -> mechanism -> invalid state or action -> symptom
```

When one chain cannot explain the pattern, separate primary causes (removal
changes the outcome) from contributing factors. A useful root cause is the
deepest supported condition you can act on inside the system, and it explains
the observed pattern better than the alternatives. Name each contributing
cause and which one the change removes.

When the origin or proposed change involves shared code, search before correction
by symbol for the same rule, query, guard, or send path. Mark each site
`in the change`, `unaffected` with a reason, or `excluded` with a reason.
Symptom-producing sites stay in the change regardless of size. Otherwise,
state that no shared code is involved.

Validate with one or more of:

- Re-run the original feedback loop after removing or controlling the cause.
- Confirm a predicted effect in a different case.
- Reintroduce the condition safely and observe the problem return.
- Compare before/after behavior against a stable baseline.
- Explain why closely related cases do not fail.

State residual uncertainty. Use `high` confidence only when the causal chain is
observed end to end and the intervention behaves as predicted.

### 6. Correct and Close

Don't mutate anything unless implementation was requested and authorized.
On handoff, re-run the causal check on your own reproduction. Stop if the origin
differs. Remove each proven origin within authorization. Diff size alone never
excludes an origin. Record rollback or stop conditions for operational changes.

As part of the root fix, sweep nearby code and configuration for earlier
symptom workarounds, guards that silence failures, and fallback branches that
have become unreachable. Check whether existing data or supported cases still
need them. Remove proven obsolete code or configuration within authorization
and flag specific out-of-scope removals with the condition that makes them safe.

A fix removes the tested origin. Catching and continuing silently, filtering
or deduplicating on read, or leaving
the defect behind a disabled flag is mitigation unless protected work is queued,
retried, or alerted. Name the remaining origin and its fix owner.
An unresolved result with the exact evidence gap or required decision, or a
labelled mitigation, is a complete investigation result.

Then:

- Re-run the Step 5 validation against the applied correction.
- Verify every site marked `in the change`.
- Remove temporary `[DEBUG-...]` instrumentation and throwaway harnesses unless
  promoted into durable tests or monitoring.
- Distinguish fixed, mitigated, monitored, and unresolved outcomes.
- Record what evidence would reopen the diagnosis.

### Report the result

Use the same investigation and validation steps for both report formats.

Default to a **Diagnosis Brief** for a bug or operational issue with a single
proven origin. Fill in each field in a short paragraph using the lengths below
as a guide. Keep probe logs and tables in working notes. Count and trim to
150–220 words total before sending, including the closing sentence.

```markdown
## Diagnosis Brief
**Root cause**: <about 50 words: one trigger -> origin -> symptom line, then one sentence of strongest direct evidence>
**Ruled out**: <up to 20 words on non-obvious disproved suspects, or omit>
**Fix & cleanup**: <about 60 words: smallest root fix, same-logic site dispositions, obsolete code removed or still to remove, and what is proposed, fixed, mitigated, monitored, or unresolved>
**Confidence & residual risk**: <about 35 words: high / medium / low with a reason based on Step 5, remaining risk, and reopen signal>
```

Use the full **Debug Summary** for multi-factor, unresolved, or high-severity
incidents, even when a single origin explains a high-severity incident.

```markdown
## Debug Summary
**Problem**: <expected versus actual>
**Evidence**: <strongest observations and baseline>
**Assumption audit**: <important verified, assumed, or contradicted beliefs>
**Root cause**: <tested causal chain>
**Same-logic sites**: <sites and dispositions, or no shared code>
**Fix class**: <fixed / mitigated / monitored / unresolved; remaining origin and fix owner for mitigation>
**Fix or experiment**: <change made, proposed, or diagnosis only>
**Validation**: <feedback loop and result>
**Residual uncertainty**: <unknowns and reopen signal>
**Confidence**: <high / medium / low with reason>
```

Keep Fix class and Same-logic sites. Omit other empty sections.

For diagnosis-only work, close either report with one plain sentence that names
the exact next scope and where the work stops. For a supported fix, use this
sentence with the actual scope filled in: “I’ve stopped at diagnosis and will
<apply and verify the specific change> if you reply `go`.” For an unresolved
cause, name the next probe or missing evidence in that sentence.

If stuck, revisit Frame, Observe, and Assumption Audit. Report the exact gap
rather than inventing variants of an exhausted hypothesis.

## Domain Appendix

| Domain | Useful feedback loop | Durable correction |
| --- | --- | --- |
| Software or data | Focused failing test, fixture, replay, trace, benchmark, or `git bisect run` | Convert the minimized reproduction into a regression test at the real seam; fix the origin of invalid state; run targeted plus proportionate regression checks |
| Service or operation | Health check, event query, bounded live probe, timing sample, or before/after metric | Contain impact, improve detection, fix the proven operational cause; define the outcome measure and review date |
| Workflow or process | One representative case traced through every handoff, plus a working comparison case | Change the smallest rule, handoff, input, ownership, or feedback mechanism that addresses the proven cause |
| Decision or forecast | Original assumptions and prediction compared with the observed outcome | Correct the invalid assumption or information flow; run the smallest reversible experiment that discriminates remaining uncertainty |
| Recurring human/team problem | Timestamped examples, trigger-response sequence, and comparison with occasions when it did not happen | Prefer clarity, incentives, environment, workload, tools, and feedback changes over warnings, blame, or personality explanations |
| Physical or external system | Safe observation, controlled substitution, elimination test, or instrument reading | Contain impact and improve detection; escalate with evidence when the cause is outside the system boundary |

## Human-In-The-Loop Observation

When a problem requires manual actions or access the agent cannot reproduce,
use `scripts/hitl-loop.template.sh` as a structured last resort:

1. Copy it to a throwaway path outside committed code.
2. Replace the prompts with the exact observation or reproduction steps.
3. Run the copy and capture the structured answers.
4. Feed those observations back into the assumption and hypothesis tables.

Don't use a human prompt as a substitute for evidence you can safely
collect yourself.
