---
name: v1-learning-from-customers
description: Use when planning or synthesizing customer discovery to test whether demand evidence is real. Triggers on "customer discovery", "customer interviews", "talk to customers", "mom test", "is this real demand", "jobs to be done".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - WebFetch
  - WebSearch
---
# Learning From Customers

Plan, audit, and synthesize customer conversations so product decisions rest on behavior, context, and commitments instead of compliments, opinions, or imagined futures.

Default mode is advisory. Do not contact customers, send messages, schedule meetings, or mutate CRM/research systems unless the user explicitly asks.

## Quick Start

For a product idea, discovery plan, interview guide, meeting notes, transcript, or pile of customer quotes:

1. Identify the product decision the research must inform.
2. Define the customer slice narrowly enough that patterns can repeat.
3. Write or audit the three most important questions for that slice.
4. Convert bad questions into past-specific questions about real behavior, current workarounds, costs, constraints, and buying process.
5. Classify evidence as fact, commitment, workflow, pain, budget/process signal, idea, compliment, or fluff.
6. Decide the next action: keep learning, narrow the segment, ask for advancement, prototype, sell, or stop.

## Input Modes

Choose one mode from the user's request:

| Mode | Use When | Output |
| --- | --- | --- |
| **Plan conversations** | The user has an idea, segment, or open research question | Customer-learning plan and conversation guide |
| **Audit questions** | The user has drafted questions or a survey/interview script | Bad-question findings and rewritten questions |
| **Synthesize notes** | The user has notes, transcripts, call summaries, or quotes | Evidence synthesis and next decision |
| **Assess demand** | The user asks whether evidence proves demand | Demand-quality review and gaps |
| **Create job spec** | The user needs Jobs-to-Be-Done framing | Job spec with progress, circumstance, competitors, anxieties, and success signals |

If the request lacks the artifact needed for the selected mode, state the missing artifact and provide the smallest useful next step.

## Workflow

### 1. Identify The Decision

Start with the decision the conversations should change:

- Is this problem worth solving?
- Which customer segment has the strongest pull?
- What current workaround, cost, or frustration exists?
- What must a new product replace, reduce, or beat?
- Is the team ready to prototype, sell, or stop?

Do not run generic discovery. Name the decision before writing questions or interpreting notes.

### 2. Slice The Customer

Define a narrow customer slice:

| Field | Questions |
| --- | --- |
| Role | Who experiences the problem directly? |
| Trigger | What event makes the problem show up? |
| Current behavior | What do they do today? |
| Context | Device, workflow, organization, budget, permissions, or environment |
| Stakes | What happens if the problem remains unsolved? |
| Access | How can conversations with this slice be found? |

If evidence is inconsistent, first check whether the team is mixing several customer slices. One conversation each with many different customer types is not the same as many conversations with one type.

### 3. Write The Three Big Questions

Choose the three highest-value unknowns for this customer slice.

Good big questions usually concern:

- The last time the problem happened.
- The current workaround and its cost.
- Who else is involved in the workflow or purchase.
- What has already been tried and abandoned.
- What would need to be fired before a new solution could be hired.
- The functional, emotional, and social progress the customer is trying to make.

Do not ask every participant the same script if reliable evidence already exists. Keep filling the picture from the highest-uncertainty edges.

### 4. Audit Questions

Flag and rewrite bad questions before the conversation.

| Bad Question Type | Why It Fails | Rewrite Pattern |
| --- | --- | --- |
| Opinion | Produces politeness or taste, not evidence | Ask about the last real instance |
| Hypothetical | Future behavior is over-optimistic | Ask what happened last time |
| Leading | Reveals the desired answer | Remove the pitch and ask about current life |
| Feature request | Turns customers into product designers | Ask what problem the idea would solve |
| Price fantasy | Treats invented willingness as budget evidence | Ask about existing spend, approval path, or replacement cost |
| Generic habit | Produces "usually" and "always" | Ask for a concrete walkthrough |

Keep the conversation about the customer's life and workflow until the learning decision requires showing the idea or product.

### 5. Run The Conversation

Use a light guide rather than a rigid script:

1. Set context briefly without pitching the solution.
2. Ask about the customer's current workflow, last occurrence, and workaround.
3. Follow concrete nouns, costs, delays, approvals, and repeated frustrations.
4. Deflect compliments by asking for specifics behind them.
5. Anchor fluff by asking when it last happened and what they did.
6. Dig beneath ideas by asking what problem they would solve and how the customer handles it now.
7. End by asking for the next useful person, artifact, or concrete advancement.

Talk less as the conversation improves. The more the agent or interviewer explains, the weaker the evidence becomes.

### 6. Capture Evidence

Separate what was observed from what was inferred.

| Evidence Type | Counts As | Does Not Count As |
| --- | --- | --- |
| Fact | Past behavior, current workflow, actual spend, named tool, concrete event | General preference |
| Pain | Repeated cost, delay, risk, embarrassment, lost money, wasted time | Mild annoyance without action |
| Workaround | Spreadsheet, manual process, hired service, internal tool, habit | "We should probably fix this" |
| Commitment | Time, money, intro, pilot, data, procurement step, scheduled next meeting | Compliment or vague enthusiasm |
| Job signal | Desired progress in a specific circumstance with functional, emotional, and social dimensions | Demographic label alone |
| Bad data | Compliment, future promise, generic claim, unsupported idea | Evidence strong enough to change a decision |

When evidence is thin, say so. Do not inflate friendly conversations into validation.

### 7. Build A Job Spec When Useful

Use Jobs-to-Be-Done framing when the product decision depends on what customers are trying to accomplish rather than what feature they requested.

```markdown
## Job Spec

Customer slice:
Triggering circumstance:
Desired progress:
Functional dimensions:
Emotional dimensions:
Social dimensions:
Current competitors / workarounds:
What must be fired:
Obstacles and anxieties:
Tradeoffs accepted:
Purchase experience needed:
Use experience needed:
Little Hire signals:
Success metrics:
```

Treat competitors broadly: products, services, spreadsheets, people, doing nothing, delaying, or cobbled-together workflows can all compete for the job.

### 8. Ask For Commitment Or Advancement

Once enough learning exists to show an idea, prototype, or offer, look for advancement:

- Schedule a concrete next meeting with the right person.
- Get an intro to a buyer, user, expert, or adjacent segment.
- Ask for time, data, pilot access, procurement steps, budget owner, or payment.
- Ask what would block adoption and who would need to approve.

If the customer remains friendly but never advances, classify the lead as unvalidated. A polite ongoing conversation is not demand.

### 9. Synthesize And Decide

End with a decision, not a pile of quotes.

Decision options:

- Keep learning: the segment is plausible, but evidence is incomplete.
- Narrow the slice: signals conflict because the customer group is too broad.
- Prototype: the problem and workflow are real, but the solution is untested.
- Sell or pilot: commitments show urgency and adoption path.
- Stop: no meaningful pain, no workaround, no budget/process, or no repeated pattern.

State what evidence would change the recommendation.

## Output Formats

### Conversation Plan

```markdown
## Customer Learning Plan

Decision:
Customer slice:
Top 3 questions:

## Conversation Guide

| Question | What It Tests | Bad Data To Watch For | Follow-Up |
| --- | --- | --- | --- |

## Evidence To Capture

## Advancement Ask

## Stop / Continue Gate
```

### Question Audit

```markdown
## Question Audit

| Question | Finding | Risk | Rewrite |
| --- | --- | --- | --- |

## Missing Questions

## Best 3 Questions
```

### Notes Synthesis

```markdown
## Customer Evidence Synthesis

Decision:
Customer slice:
Verdict:

## Evidence

| Claim | Evidence | Type | Strength | Notes |
| --- | --- | --- | --- | --- |

## Bad Data

## Job Spec

## Next Action
```

Evidence strength:

- **Strong:** repeated behavior, costly workaround, real spend, or concrete commitment.
- **Medium:** credible past behavior from a fitting customer slice.
- **Weak:** opinion, unverified claim, noncommittal pain, or single anecdote.
- **Bad data:** compliment, hypothetical, generic future promise, or unsupported idea.

## Anti-Patterns

- Asking whether the idea is good.
- Asking what customers would do in the future.
- Treating compliments as validation.
- Letting feature requests become requirements without finding the underlying problem.
- Interviewing a broad market and expecting coherent patterns.
- Pitching before learning the current workflow.
- Keeping customer learning in one person's head.
- Reporting quotes without separating observation, inference, and team opinion.

## Chaining

- Use `v1-interview-me` first when the user needs to clarify the product idea or learning decision.
- Use `v1-testing-prototypes` after a prototype exists and the team needs observed task/value evidence.
- Use `v1-prd` after customer evidence is strong enough to write build requirements.
- Use `v1-strategy-review` when customer learning changes the wedge, scope, or product direction.

## When Not To Use This Skill

- Do not use for general feature specification once demand is already clear; use `v1-prd`.
- Do not use for live prototype-test planning or synthesis; use `v1-testing-prototypes`.
- Do not use for broad strategy critique unless the immediate question is customer evidence quality; use `v1-strategy-review`.
- Do not use for operational bottleneck or throughput diagnosis; use `v1-diagnosing-constraints`.

## Examples

**Bad question rewrite**

Input: "Would you pay for a dashboard that automates this?"

Output: Ask when the workflow last happened, what they used, how long it took, who cared about the output, and what budget or approval path existing tools go through.

**Weak evidence**

Input: "Everyone loved the idea and said they would use it."

Output: Classify as bad data unless notes include past behavior, current workaround, cost, budget owner, or concrete next step.

**Segment problem**

Input: Ten conversations produce ten unrelated requested features.

Output: Check whether the team is mixing several customer slices. Narrow by trigger, role, workflow, or current workaround before drawing product conclusions.
