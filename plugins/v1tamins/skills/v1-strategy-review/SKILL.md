---
name: v1-strategy-review
description: Use when reviewing a plan, PRD, product direction, or implementation proposal for strategy, scope, user value, ambition, and hidden assumptions. Triggers on "strategy review", "CEO review", "founder review", "think bigger", "rethink this", "is this ambitious enough".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - AskUserQuestion
---
# Strategy Review

Review a plan like a founder who cares whether the work creates real user value, not just whether it is internally consistent.

Use after `v1-interview-me` when the idea is still fluid. Use before implementation when the plan already exists but scope, ambition, or user value are questionable.

## Workflow

### 1. Load the Plan and Context

Read the plan, PRD, ticket, or proposal. Then inspect nearby context:
- Related docs in `docs/`, `README.md`, `CLAUDE.md`, or `AGENTS.md`
- Related code, if the plan proposes implementation work
- Related issues or tickets, if the user provided them

Do not review from the title alone.

### 2. Choose Scope Posture

Choose one posture and state it clearly:

| Posture | Use When |
|---------|----------|
| **Expand** | The idea is directionally right but undershoots the user value |
| **Selective expansion** | The baseline is good, but a few adjacent improvements may be worth adding |
| **Hold scope** | The scope is right, and the goal is rigor |
| **Reduce** | The plan is overbuilt, vague, or solving a proxy problem |

If the user gave explicit posture language, follow it. Otherwise default to selective expansion for product features, hold scope for bug fixes and refactors, and reduce for plans that touch many files without clear user impact.

Do not add scope silently. Propose scope changes and get approval before editing a plan to include them.

### 3. Premise Challenge

Answer these before detailed review:
- Is this the right problem to solve?
- Who is the user, and what painful status quo are they living with now?
- What would happen if we did nothing?
- Is the plan solving the user outcome directly, or solving an internal proxy?
- What existing code, workflow, or artifact already solves part of this?

If the plan lacks demand evidence, say so. Interest, taste, or internal excitement is not demand.

### 4. Generate Alternatives

Produce at least two implementation or product approaches:
- **Minimal viable:** fewest moving parts that proves value
- **Planned approach:** what the doc currently proposes
- **Ideal version:** the 12-month direction or best product shape, if meaningfully different

For each approach, include effort, risk, reuse of existing code, what it validates, and what it defers.

Recommend one approach. Tie the recommendation to user value, speed to learning, and reversibility.

### 5. Review Dimensions

Evaluate the plan across these dimensions:
- **Demand:** evidence that someone needs this now
- **Status quo:** current workaround and cost
- **Wedge:** smallest useful version
- **Differentiation:** why this is not just another version of the obvious thing
- **Scope:** work that must ship together vs. follow-up
- **Complexity:** unnecessary files, abstractions, dependencies, or coordination
- **Implementation ambiguity:** decisions the builder will hit in the first hours of work
- **Risk:** security, data, reliability, support, rollout, and rollback concerns
- **Validation:** how success will be observed quickly
- **Future fit:** whether this gets more valuable as the world changes

For each material issue, include what would change your mind.

### 6. Expansion Scan

Only for expand or selective expansion posture, look for:
- A 10x version that delivers much more value for modest extra effort
- Small delight or trust improvements that take little engineering time
- Platform moves that make future features easier
- Distribution or adoption hooks that help real users find or use the work

Separate expansion candidates into:
- **Recommend adding now**
- **Defer with notes**
- **Skip**

Ask before adding any recommended expansion to the plan.

### 7. Edit the Plan When Asked

If the user asks you to update the plan, edit the existing artifact rather than creating a parallel strategy doc.

Preserve the original structure unless it is actively confusing. Add a `Strategy Review` section only when the plan has no obvious place for the findings.

Record decisions explicitly:
- Accepted scope
- Deferred scope
- Rejected scope
- Open questions
- Recommended next action

### 8. Output Format

Use this structure:

```markdown
## Strategy Review

Verdict: [one sentence]
Posture: [Expand / Selective expansion / Hold scope / Reduce]

### Must Fix
- [Issue, why it matters, recommended change]

### Scope Recommendations
- Add now: [...]
- Defer: [...]
- Skip: [...]

### Alternatives
1. [Minimal viable approach]
2. [Current/planned approach]
3. [Ideal approach]

### Open Questions
- [Question, owner if known, why it blocks progress]

### Next Action
[One concrete assignment]
```

If there are no serious issues, say that clearly, then list residual risks.
