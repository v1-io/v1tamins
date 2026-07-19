---
name: v1-diagnosing-constraints
description: Use when a process, funnel, queue, or delivery system is stuck and needs throughput-bottleneck diagnosis using Theory of Constraints. Triggers on "find the bottleneck", "too much WIP", "throughput is stuck", "where is the constraint", "our funnel is stuck". For a broader expected-versus-actual failure or root-cause question, use v1-debug.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---
# Diagnosing Constraints

Find the constraint that governs system throughput, then focus improvement work where it can change the whole system.

Default mode is diagnostic and advisory. Do not rewrite plans, change process rules, or edit files unless the user explicitly asks for implementation.

## Quick Start

1. Define the system and its goal.
2. Map the flow of work from request to delivered outcome.
3. Identify the constraint using queues, starvation, blocking, rework, chronic expedites, or scarce decision points.
4. Apply the focusing loop: identify, exploit, subordinate, elevate, repeat.
5. Validate with system-level measures, not local utilization.

Use this skill for software delivery, support queues, sales funnels, product roadmaps, operations, services, and manufacturing-like workflows. Translate terms to the user's domain.

## Core Measures

Choose domain-appropriate measures before recommending action:

| Measure | Meaning | Software/Service Translation |
| --- | --- | --- |
| Throughput | Rate at which the system produces the goal outcome | Shipped value, resolved cases, qualified revenue, completed decisions |
| Inventory / WIP | Work or money trapped inside the system | Open tickets, half-built features, pending approvals, queued work |
| Operating expense | Cost to turn WIP into throughput | Team time, cloud spend, vendor cost, management attention |
| Lead time | Time from request/release to done | Cycle time, SLA time, decision latency |
| Due-date performance | Reliability of promised delivery | SLA hit rate, plan reliability, forecast accuracy |

Never optimize one measure in isolation. Treat local utilization, activity, and cost-per-unit as suspect until they are tied to throughput, WIP, and operating expense.

## Workflow

### 1. Establish The System Boundary

Define:

- Goal outcome: what the system exists to produce.
- Start and end points: where work enters and where value is realized.
- Demand: what the system is asked to handle.
- Promise: deadline, SLA, revenue target, customer expectation, or roadmap commitment.
- Current symptoms: late work, queues, expedites, idle people, rework, inventory, missed targets, or fire drills.

If the goal is unclear, stop and clarify it before diagnosing the constraint.

### 2. Map Dependent Events

Build a simple flow map:

```text
Input -> Step A -> Step B -> Step C -> Delivered outcome
```

For each step, capture:

- Required input from the previous step.
- Queue or wait before the step.
- Work time, review time, approval time, and handoff time.
- Failure/rework rate.
- Owner or scarce resource.
- Whether downstream work can proceed without it.

Mark where variability accumulates. In dependent flows, small delays do not automatically average out; they often become queues.

### 3. Find Constraint Candidates

Use observable evidence before theories:

- Work piles up in front of a step.
- Downstream steps are starved for the right input.
- Expeditors repeatedly chase the same area, person, queue, or approval.
- Work is often marked urgent, blocked, or "drop everything."
- The same specialist, environment, reviewer, customer, machine, or decision forum is always needed.
- Lead time is dominated by queue or wait, not actual work time.
- Local teams look busy while shipped output remains flat.
- The process creates work earlier than the constraint can consume it.

Do not require perfect data. Start with candidate constraints, then verify with targeted evidence.

### 4. Apply The Focusing Loop

Use this order. Do not skip to adding capacity before exploitation and subordination.

1. **Identify** the system constraint.
   - Name the constraint and the evidence.
   - Decide whether it is physical, policy, market, skill, attention, approval, data, or demand.

2. **Exploit** the constraint.
   - Protect it from bad inputs, rework, idle time, low-value work, interruptions, and unclear priorities.
   - Put quality checks before the constraint when defects would consume scarce capacity.
   - Ensure the constraint always works on the highest-throughput work available.

3. **Subordinate** everything else to that decision.
   - Release work at the rate the constraint can consume.
   - Stop optimizing non-constraints for utilization.
   - Change priorities, incentives, batch sizes, and handoffs so they support the constraint.

4. **Elevate** the constraint.
   - Add capacity, automation, tooling, training, outsourcing, policy change, or scope reduction only after exploitation/subordination are insufficient.

5. **Repeat** when the constraint moves.
   - Re-run the diagnosis.
   - Remove stale policies created for the old constraint.
   - Watch for inertia becoming the new constraint.

### 5. Test Common Failure Modes

Actively check for these traps:

- **Balanced-capacity trap:** trying to keep every person or resource fully utilized.
- **Local-efficiency trap:** saving time at a non-constraint and treating it as system improvement.
- **Batch-size trap:** large batches reduce setup churn but inflate queue/wait time and WIP.
- **Expedite trap:** priority becomes "hot, hotter, drop everything," destroying predictability.
- **Measurement trap:** cost accounting or vanity metrics make worse system decisions look efficient.
- **Policy-constraint trap:** the apparent bottleneck is caused by release rules, incentives, approvals, or definitions of done.
- **Inertia trap:** rules that helped the old constraint remain after the constraint has moved.

### 6. Recommend Action

Keep recommendations focused. The best answer is usually a small sequence:

1. What to stop doing.
2. What to protect or prioritize at the constraint.
3. What non-constraints must subordinate.
4. What to measure for one feedback cycle.
5. What would justify elevating capacity.

Do not propose broad transformation, reorgs, dashboards, or automation until the constraint diagnosis shows they are required.

## Output Format

```markdown
## Constraint Diagnosis

System goal:
Current symptom:
Likely constraint:
Evidence:
Confidence: N/5

## Flow Map

| Step | Queue/Wait | Work Time | Owner | Evidence | Constraint Signal |
| --- | --- | --- | --- | --- | --- |

## Focusing Plan

1. Identify:
2. Exploit:
3. Subordinate:
4. Elevate:
5. Repeat / inertia check:

## Measures To Watch

| Measure | Current | Target / Direction | How To Collect |
| --- | --- | --- | --- |

## Open Questions

- ...
```

If evidence is weak, label the diagnosis as a hypothesis and propose the smallest data collection that would confirm or falsify it.

## Chaining

- Use `v1-interview-me` first when the user needs a guided conversation to define the system boundary, goal, or symptom.
- Use `v1-strategy-review` after the constraint diagnosis raises broader product, market, roadmap, or business-model tradeoffs.
- Use `v1-debug` when the apparent constraint is actually a specific failure needing root-cause diagnosis — a bug, regression, broken handoff, or other expected-versus-actual gap.
- Use `v1-prd` when the diagnosis produces concrete product or process requirements that need implementation-ready specification.

## When Not To Use This Skill

- Do not use for general feature fleshing or office-hours questioning; use `v1-interview-me`.
- Do not use for root-cause debugging of a specific failure, software or otherwise; use `v1-debug`.
- Do not use for customer-demand discovery or JTBD synthesis; use `v1-learning-from-customers`.
- Do not use for broad strategy review unless the immediate task is to identify the system constraint.

## Examples

**Software delivery**

Symptom: Many engineers are busy, but production releases are late.

Likely constraint: Review or deploy approval queue.

Action: Protect review capacity, limit WIP entering review, stop starting new branches until review queue clears, then measure lead time and release rate.

**Support operations**

Symptom: Ticket backlog grows even though triage is fast.

Likely constraint: Escalation specialist or product decision loop.

Action: Route only high-value escalations to the specialist, improve pre-escalation quality, and throttle new triage work if it only creates more waiting.

**Roadmap planning**

Symptom: Many initiatives are "in progress" but few reach customers.

Likely constraint: Decision clarity, integration capacity, or customer validation.

Action: Pick the constraint, freeze lower-value starts, subordinate roadmap sequencing, and validate using shipped outcomes rather than activity.
