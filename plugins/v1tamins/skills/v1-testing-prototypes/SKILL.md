---
name: v1-testing-prototypes
description: Use when planning or synthesizing user tests for prototypes, mockups, clickable demos, product concepts, design flows, landing pages, or early product specs. Triggers on "test this prototype", "prototype testing", "user test plan", "validate this product idea", "test with users".
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - WebFetch
  - WebSearch
---
# Testing Prototypes

Plan and synthesize prototype tests that reveal whether a product idea is valuable, usable, and feasible before engineering commits to building it.

## Output Contract

Default output:

```markdown
## Prototype Test Plan

### Objective
[What must be learned before build/ship decisions.]

### Target Users
[Primary users, excluded users, and screener criteria.]

### Tasks
| Task | What It Tests | Success Signal | Watch For |
| --- | --- | --- | --- |

### Value Questions
[Questions asked after use, not before, to test whether users care.]

### Facilitation Rules
[How to avoid leading, rescuing, or turning the session into design critique.]

### Evidence Capture
[Observation format, severity scale, and synthesis table.]

### Decision Gate
[Proceed, iterate, retest, or shelve.]
```

If the user already ran sessions, produce a synthesis instead: findings, evidence, severity, next prototype changes, and whether another round is needed.

## Workflow

### 1. Identify the Decision

Start with the decision the prototype test should support:

- Is this problem worth solving?
- Can target users understand and complete the core tasks?
- Do users value the solution enough to switch, pay, recommend, or continue?
- Which design or product risks need evidence before build?
- Is the prototype coherent enough to become the product spec?

Do not run a generic preference test. Prototype testing is for evidence that changes product decisions.

### 2. Inspect the Prototype

Review the artifact before writing the plan:

- Clickable URL, Figma, local app, screenshots, wireframes, demo script, spec, or landing page.
- Primary flow and entry points.
- Known dead ends or fake backend behavior.
- Target persona and intended job.
- Build decision, launch decision, or iteration decision the team is facing.

If no artifact exists, produce a testable-prototype checklist before a user-test plan.

### 3. Separate Test Types

Cover the three risks separately:

| Risk | Test Method | Evidence |
| --- | --- | --- |
| Value | Users care after seeing/using the prototype | Pull, willingness to switch/pay/recommend, emotional reaction, urgency |
| Usability | Users can complete key tasks without help | Task completion, hesitation, wrong turns, abandonment, language mismatch |
| Feasibility | The team can build the needed behavior | Engineer review, risky assumptions, integration/data/performance constraints |

Do not treat stated preference as value evidence. Watch what users do, then ask why.

### 4. Define Target Users and Screener

Write a short screener that filters for the real target user:

- Current behavior: how they solve the problem today.
- Frequency and pain: how often the problem appears and how costly it is.
- Context: role, company type, device, environment, or workflow.
- Exclusions: friends, insiders, early adopters, or people outside the target profile unless deliberately testing edge users.

Prefer a small number of high-fit users over many weak-fit users.

### 5. Write Tasks

Tasks should put users in use mode:

- Use realistic scenarios, not feature tours.
- Ask users to accomplish goals, not evaluate screens.
- Start with the user's current mental model when possible.
- Keep the most important tasks first.
- Include success signals and failure signals for each task.
- Capture the action cycle for important tasks using the shared [interaction review taxonomy](../v1-reviewing-usability/references/interaction-review-taxonomy.md).

Avoid questions like "What would you change?" until after observed use. Design suggestions are secondary to evidence of comprehension, value, and behavior.

For each primary task, add one taxonomy-backed usability observation row so the note-taker watches for goal cues, expected first action, feedback needed, and likely failure mechanism.

### 6. Facilitate Without Leading

Use these rules during sessions:

- Say the prototype is being tested, not the participant.
- Keep the intro short so first impressions remain untainted.
- Stay quiet when the participant struggles.
- Do not rescue the participant unless the session is no longer producing useful evidence.
- Reflect questions back instead of answering them.
- Ask what the participant expected when they click into a dead end.
- Ask what they expected to happen after meaningful actions, especially submits, saves, deletes, automation triggers, or mode switches.
- Capture body language, hesitation, confusion, workarounds, and moments of excitement.
- Capture the failed mechanism from the interaction review taxonomy when confusion appears.
- Have one facilitator and one note taker when possible.

### 7. Ask Value Questions After Use

Ask value questions after the participant has experienced the prototype:

- What do they use today instead?
- How much better or worse is this than the current alternative?
- What would make them switch?
- What would stop them from using it?
- Who else would need to approve or adopt it?
- How likely are they to recommend it, and why?
- If pricing is relevant, what budget or willingness-to-pay signal exists?

Use numeric scales only when they help compare rounds. Always capture the explanation behind the number.

### 8. Synthesize Evidence

Use this synthesis table:

| Finding | Evidence | Risk Type | Severity | Prototype Change | Retest? |
| --- | --- | --- | --- | --- | --- |

Severity:

- P0: invalidates the concept or target user.
- P1: blocks the primary task or value perception.
- P2: creates confusion but has a plausible fix.
- P3: polish or copy issue.

Separate:

- Observed behavior.
- Participant explanation.
- Facilitator inference.
- Team opinion.

For usability findings, include the failed mechanism when it is clear. Use the interaction review taxonomy instead of inventing new labels per test.

### 9. Decide What Happens Next

Recommend one next action:

- Proceed to build: primary tasks work, value is clear, feasibility risks are resolved.
- Iterate and retest: value exists but usability or concept clarity needs work.
- Change target user: wrong persona, but another user segment showed stronger pull.
- Reframe the problem: the observed need differs from the proposed solution.
- Shelve the idea: users do not care enough or the solution cannot become viable.

As a practical heuristic, when several consecutive target users understand the value and complete the key tasks without help, the prototype is usually ready for the next build decision. Do not require artificial statistical certainty for qualitative discovery work.

## Anti-Patterns

- Testing stakeholder taste instead of target-user behavior.
- Starting with a feature tour.
- Asking users what to build before showing a concrete solution.
- Treating focus-group consensus as product evidence.
- Letting the facilitator explain confusing parts of the prototype.
- Promoting a prototype test into an E2E test. Use `v1-e2e-testing` for built product flows.
- Shipping because users were polite. Look for behavior, pull, and task success.

## Chaining

- Use `v1-interview-me` first when the idea is too vague to define a prototype objective.
- Use `v1-prd` after prototype evidence supports a build decision.
- Use `v1-strategy-review` when the prototype test raises broader product or business tradeoffs.
- Use `v1-e2e-testing` after the prototype becomes implemented product behavior.
