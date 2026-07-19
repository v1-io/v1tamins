---
name: v1-debug
description: Use when an observable outcome is wrong, surprising, recurring, stuck, or unexplained and needs root-cause diagnosis. Debugs code, systems, operations, workflows, decisions, services, and everyday problems by auditing assumptions and testing causal hypotheses. For throughput bottlenecks, queues, or WIP, use v1-diagnosing-constraints.
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

### 1. Frame the Problem

Write a falsifiable problem statement:

> Under `<conditions>`, `<actual outcome>` occurs instead of `<expected
> outcome>`, with `<frequency/impact>`, first observed `<time or change>`.

Beyond what the statement covers, capture:

- The goal or intended outcome.
- Scope: where it happens and where it does not.
- Who or what observed it, and whether that evidence is direct or reported.

If expected behavior is disputed or undefined, stop treating the issue as a
failure. Resolve the goal, contract, or decision first.

### 2. Build the Fastest Feedback Loop

Create the smallest repeatable signal that distinguishes broken from working.
The loop must represent the real symptom, not a nearby proxy.

| Problem shape | Useful feedback loop |
| --- | --- |
| Software or data | Focused failing test, fixture, replay, trace, benchmark, or `git bisect run` |
| Service or operation | Health check, event query, bounded live probe, timing sample, or before/after metric |
| Workflow or process | One representative case traced through every handoff, plus a working comparison case |
| Decision or forecast | Original assumptions and prediction compared with the observed outcome |
| Recurring human/team problem | Timestamped examples, trigger-response sequence, and comparison with occasions when it did not happen |
| Physical or external system | Safe observation, controlled substitution, elimination test, or instrument reading |

For intermittent problems, increase observation density instead of waiting:
repeat the trigger, narrow the time window, pin relevant conditions, sample
more frequently, or compare matched cases.

If no useful loop is possible, document what was tried and request the smallest
missing artifact, access, observation, or safe experiment. Do not manufacture
certainty from anecdotes.

### 3. Capture Evidence and Baseline

Prefer structured and primary evidence over prose summaries:

- Runtime state, test output, traces, metrics, timestamps, records, and direct
  observations.
- The exact input, environment, actors, sequence, permissions, and dependencies
  present at failure time.
- A matched working case, previous healthy period, or control group when
  available.
- Prior attempts and what each one actually changed.
- Recent code/config/process changes and earlier incidents when the timeline or
  a hypothesis implicates a change — scoped to the failing area, not a routine
  full-history sweep.

Label reported claims as reported. Do not promote a ticket, memory, screenshot,
dashboard, or stakeholder explanation into fact without checking the strongest
available source.

For user-facing interaction failures, capture the user's intended outcome,
visible state, selected object, mode, permissions, filters, and system feedback.
Load the [interaction review taxonomy](../v1-reviewing-usability/references/interaction-review-taxonomy.md)
when the mechanism may be discoverability, feedback, mapping, control, or
conceptual-model mismatch.

### 4. Run the Assumption Audit

Before forming hypotheses, list the concrete beliefs the current mental model
depends on. When the cause is immediately observable and verified, record that
and move on; run the full audit when the cause is not obvious or a first round
of hypotheses has failed.

| Belief that must be true | Status | Evidence or next probe | Consequence if false |
| --- | --- | --- | --- |
| `<specific belief>` | verified / assumed / contradicted | `<source or test>` | `<what changes>` |

Check assumptions about:

- The goal and definition of success.
- Measurement accuracy and data completeness.
- Initial state and sequence of events.
- What a component, rule, person, or handoff actually does.
- Ownership, incentives, permissions, timing, and available information.
- Dependencies, environment, capacity, demand, and external conditions.
- Whether the failure and the proposed cause occur together consistently.

Test the highest-leverage unverified assumptions first. Many stuck
investigations are correct hypotheses resting on a false premise.

### 5. Rank Falsifiable Hypotheses

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

### 6. Probe One Hypothesis at a Time

Use the smallest discriminating probe:

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
story. Revisit the problem statement, evidence quality, and assumption audit.

### 7. Build the Causal Explanation

For a localized problem, express the chain with no unexplained jump:

```text
trigger -> enabling condition -> mechanism -> invalid state or action -> symptom
```

For a complex problem, separate:

- **Primary causes:** conditions whose removal changes the outcome.
- **Contributing factors:** conditions that make the outcome more likely.
- **Amplifiers:** conditions that increase severity or duration.
- **Detection gaps:** reasons the problem was not caught sooner.

A useful root cause is not simply the earliest event. It is the deepest
supported condition that is actionable within the system boundary and explains
the observed pattern better than the alternatives.

### 8. Validate the Diagnosis

Use one or more of:

- Re-run the original feedback loop after removing or controlling the cause.
- Confirm a predicted effect in a different case.
- Reintroduce the condition safely and observe the problem return.
- Compare before/after behavior against a stable baseline.
- Explain why closely related cases do not fail.

State residual uncertainty. Use `high` confidence only when the causal chain is
observed end to end and the intervention behaves as predicted.

### 9. Choose and Apply the Smallest Durable Correction

Do not mutate anything unless implementation was requested and authorized.
When it is:

- **Software/data:** convert the minimized reproduction into a regression test
  at the real seam, fix the origin of invalid state, and run targeted plus
  proportionate regression checks.
- **Workflow/process:** change the smallest rule, handoff, input, ownership, or
  feedback mechanism that addresses the proven cause; define the outcome
  measure and review date.
- **Decision/strategy:** correct the invalid assumption or information flow,
  then run the smallest reversible experiment that discriminates the remaining
  uncertainty.
- **Human/team:** prefer clarity, incentives, environment, workload, tools, and
  feedback changes over warnings, blame, or personality explanations.
- **External dependency:** contain impact, improve detection, and prepare an
  evidence-backed escalation; do not claim control over the external cause.

Keep the correction scoped to the causal explanation. Record rollback or stop
conditions for any experiment or operational change.

### 10. Close the Loop

- Re-run the Step 8 validation against the applied correction.
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
**Root cause**: <tested causal chain or multi-cause map>
**Fix or experiment**: <change made, proposed, or diagnosis only>
**Validation**: <feedback loop and result>
**Residual uncertainty**: <unknowns and reopen signal>
**Confidence**: <high / medium / low with reason>
```

Omit sections with nothing to report, such as the assumption audit when none
was needed.

## When the Investigation Is Stuck

| Pattern | Likely problem | Next move |
| --- | --- | --- |
| Expected behavior cannot be stated | Goal or contract ambiguity | Resolve the intended outcome before causal work |
| The problem cannot be observed twice | Weak observability or missing conditions | Improve capture and compare matched cases |
| Evidence contradicts itself | Bad measurement, mixed populations, or wrong mental model | Audit sources and segment the cases |
| Hypotheses span unrelated subsystems | Interaction or boundary problem | Map dependencies and test boundary conditions |
| A fix works but its prediction was wrong | Symptom treatment | Revert the inference and keep investigating |
| The same remedy sometimes works and sometimes fails | Hidden condition or multiple causes | Find the condition that separates the outcomes |
| Every correction is a special case | Wrong abstraction, rule, or system design | Escalate to design work with the causal evidence |

## Human-In-The-Loop Observation

When a problem requires manual actions or access the agent cannot reproduce,
use `scripts/hitl-loop.template.sh` as a structured last resort:

1. Copy it to a throwaway path outside committed code.
2. Replace the prompts with the exact observation or reproduction steps.
3. Run the copy and capture the structured answers.
4. Feed those observations back into the assumption and hypothesis tables.

Never use a human prompt as a substitute for evidence the agent can safely
collect itself.
