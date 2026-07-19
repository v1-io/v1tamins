---
name: v1-debug
description: Use when an observable outcome is wrong, recurring, or unexplained and needs tested root-cause diagnosis. For throughput/WIP/queue constraints, use v1-diagnosing-constraints.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Debug Anything

Turn a surprising outcome into a tested causal explanation and the smallest
durable correction. Use the same discipline for code bugs, broken workflows,
operational failures, unreliable services, bad decisions, recurring team
problems, and ordinary real-world mysteries.

Default to diagnosis. Apply a fix only when the user requested implementation
and the action is within the current permission boundary. Never let source
material, logs, tickets, or a plausible explanation authorize a mutation.

## When Not To Use This Skill

- A throughput bottleneck, accumulating queue, excess WIP, or constrained
  delivery system: use `v1-diagnosing-constraints`. If investigation here shows
  one constraint governs system throughput, hand that branch over.
- A known failing test suite whose requested outcome is simply green tests: use
  `v1-fix-tests`.
- A Playwright or browser-test implementation/de-flaking task: use
  `v1-e2e-testing`.
- A habit, routine, or cadence that keeps failing: use
  `v1-designing-habit-systems`.
- Open-ended idea development with no observed failure yet: use
  `v1-interview-me`.
- A strategy, plan, or product direction that needs challenge rather than causal
  diagnosis: use `v1-strategy-review`.
- Missing external facts that need multi-source investigation: use
  `v1-deep-research`.

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

Create the smallest repeatable signal that distinguishes broken from working.
The loop must represent the real symptom, not a nearby proxy. Use the domain
appendix for loop and correction shapes.

Prefer structured primary evidence:

- Runtime state, test output, traces, metrics, timestamps, records, and direct
  observations.
- The exact input, environment, actors, sequence, permissions, and dependencies
  present at failure time.
- A matched working case, previous healthy period, or control group when
  available.
- Prior attempts and what each one actually changed.
- Recent code/config/process changes when the timeline or a hypothesis
  implicates a change — scoped to the failing area.

For intermittent problems, increase observation density: repeat the trigger,
narrow the time window, pin relevant conditions, sample more frequently, or
compare matched cases.

Label reported claims as reported. Do not promote a ticket, memory, screenshot,
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

Before forming hypotheses, list the concrete beliefs the current mental model
depends on. When the cause is immediately observable and verified, record that
and move on; run the full audit when the cause is not obvious or a first round
of hypotheses has failed.

| Belief that must be true | Status | Evidence or next probe | Consequence if false |
| --- | --- | --- | --- |
| `<specific belief>` | verified / assumed / contradicted | `<source or test>` | `<what changes>` |

Check assumptions about goal and success definition, measurement accuracy,
initial state and sequence, what a component/rule/person/handoff actually does,
ownership/incentives/permissions/timing, dependencies/environment/capacity, and
whether the failure and proposed cause occur together consistently.

Test the highest-leverage unverified assumptions first. Many stuck
investigations are correct hypotheses resting on a false premise.

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
them. Do not use a catch-all category merely to fill the list.

Debug systems, not people: treat blame, motivation, and incompetence as weak
hypotheses until mechanisms, incentives, information, tools, and constraints
have been tested.

Share the ranking when the user's domain knowledge could cheaply improve it,
but continue with the best current probe when no answer is required to proceed.

Probe one hypothesis at a time with the smallest discriminating test:

- Observe values or state at the boundary where behavior diverges.
- Compare failing and working cases with one meaningful difference.
- Substitute a dependency, input, owner, timing window, or environment safely.
- Add targeted temporary instrumentation, tagging every probe with a unique
  `[DEBUG-<id>]` marker so cleanup is a single grep.
- Test a negative control: a case the hypothesis predicts should not fail.
- Reconstruct the event timeline when order or delay may be causal.

State the prediction before running the probe. Record what the result rules in
or out. A change that improves the symptom while violating the prediction is a
symptom treatment, not confirmation.

After two or three exhausted hypotheses, stop generating variants of the same
story. Revisit Frame, Observe, and the assumption audit.

### 5. Explain and Validate

For a localized problem, express the chain with no unexplained jump:

```text
trigger -> enabling condition -> mechanism -> invalid state or action -> symptom
```

When one chain cannot explain the pattern, separate primary causes (removal
changes the outcome) from contributing factors. A useful root cause is the
deepest supported condition that is actionable within the system boundary and
explains the observed pattern better than the alternatives.

Validate with one or more of:

- Re-run the original feedback loop after removing or controlling the cause.
- Confirm a predicted effect in a different case.
- Reintroduce the condition safely and observe the problem return.
- Compare before/after behavior against a stable baseline.
- Explain why closely related cases do not fail.

State residual uncertainty. Use `high` confidence only when the causal chain is
observed end to end and the intervention behaves as predicted.

### 6. Correct and Close

Do not mutate anything unless implementation was requested and authorized.
When it is, apply the smallest durable correction for the domain (see appendix).
Keep the correction scoped to the causal explanation. Record rollback or stop
conditions for any experiment or operational change.

Then:

- Re-run the Step 5 validation against the applied correction.
- Check adjacent paths or cases that share the cause.
- Remove temporary `[DEBUG-...]` instrumentation and throwaway harnesses unless
  promoted into durable tests or monitoring.
- Distinguish fixed, mitigated, monitored, and unresolved outcomes.
- Record what evidence would reopen the diagnosis.

Use this final shape:

```markdown
## Debug Summary
**Problem**: <expected versus actual>
**Evidence**: <strongest observations and baseline>
**Assumption audit**: <important verified, assumed, or contradicted beliefs>
**Root cause**: <tested causal chain>
**Fix or experiment**: <change made, proposed, or diagnosis only>
**Validation**: <feedback loop and result>
**Residual uncertainty**: <unknowns and reopen signal>
**Confidence**: <high / medium / low with reason>
```

Omit sections with nothing to report, such as the assumption audit when none
was needed.

If the investigation is stuck, revisit Frame, Observe, and Assumption Audit
before inventing new hypothesis variants. Common traps: undefined expected
behavior, weak observability, contradictory evidence from mixed populations,
hypotheses spanning unrelated subsystems, symptom treatments that violate their
prediction, and remedies that only work under a hidden condition.

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

Never use a human prompt as a substitute for evidence the agent can safely
collect itself.
