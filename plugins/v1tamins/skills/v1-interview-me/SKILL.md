---
name: v1-interview-me
description: Use when an idea, feature request, ticket, or concept needs office-hours-style questioning before planning. Triggers on "interview me about X", "help me spec out Y", "I have an idea for Z", "flesh out this idea", "is this worth building".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - AskUserQuestion
  - Skill
---
# Interview Me

Collaboratively refine ideas through structured questioning, helping the agent understand the idea and the user crystallize their thinking. The interview process itself is valuable, not just the final deliverable.

## Usage

Typical invocations:
- Claude Code: `/v1-interview-me [TICKET_ID or idea]`
- Codex: invoke `v1-interview-me` from the skills menu or use `$v1-interview-me [TICKET_ID or idea]`

```text
/v1-interview-me
/v1-interview-me <TICKET_ID>
/v1-interview-me <paste idea or feature description>
```

Can also be triggered conversationally: "I have an idea for X", "help me spec out Y", "flesh out this concept".

## Before the interview

**Understand the starting point.** Read any provided context and identify what's stated vs. assumed, the domain, and the stakeholders.

**Gather context first — explore, don't ask.** If a question can be answered by reading the codebase, the issue tracker, or existing docs, explore instead of asking. Only interview for what requires the user's judgment, intent, or domain knowledge.

## Choose the interview posture

Classify the session before asking the first question:

| Posture | Use When | Interview Bias |
|---------|----------|----------------|
| **Startup diagnostic** | Customer, revenue, fundraising, market, internal sponsor, adoption, or "worth building" language appears | Clarify the learning decision; switch to `v1-learning-from-customers` for discovery planning, question audits, notes synthesis, or demand review |
| **Builder exploration** | Side project, learning, hackathon, open source, creative tool, or "cool thing" language appears | Delight, fastest demo, who to show, surprising combinations, next build step |
| **Implementation spec** | User already knows this should be built | Decisions, constraints, edge cases, integration, validation |
| **Socratic operational diagnostic** | Bottleneck, queue, WIP, throughput, "everything is urgent", process failure, handoff delay, or stuck team language appears | Clarify the system boundary; switch to `v1-diagnosing-constraints` for constraint diagnosis |

Default to **Startup diagnostic** when the user asks whether something is worth building. Default to **Builder exploration** when the user wants to riff before committing. Switch postures mid-interview if the user's answers reveal a different job.

For startup-diagnostic sessions, ask only enough to identify the learning decision, target customer slice, and current evidence gap. If the user wants a discovery plan, question audit, interview synthesis, demand assessment, or JTBD job spec, switch to `v1-learning-from-customers`.

**Builder exploration prompts:**
- What's the version you would be excited to show someone this week?
- What would make the first demo feel surprisingly good?
- What's the fastest path to something usable?
- What existing thing is closest, and what should be different?
- What would the 10x version include if time were free?

For operational-diagnostic sessions, ask only enough to identify the system goal, boundary, and visible symptom. If the user wants the diagnosis rather than interview notes, switch to `v1-diagnosing-constraints`.

End every posture with one concrete assignment: the next thing the user or agent should do.

## Run the interview loop

Once the posture is set, run the loop in [interview-loop.md](references/interview-loop.md): map the decision tree, open with the right first question, calibrate depth, and conduct the interview one focused round at a time. Two mechanics that define the loop:

- **Every question carries a recommended answer** — the first AskUserQuestion option is your proposed answer, labeled `(Recommended)`, so the user reacts to a concrete proposal. This is the default questioning shape, not an occasional flourish.
- **Close every decision** (decided / deferred / blocked) before moving on, and share a progressive-synthesis checkpoint every 2-3 rounds.

The loop also holds uncertainty handling, the question-category tables, constructive-challenge and pivot guidance, and the specification template.

## Recognize completion

Stop interviewing when:
- Core user journeys are mapped
- Error handling and edge cases are addressed (or marked TBD appropriately)
- Integration points and dependencies are identified
- Success criteria and metrics are defined
- Scope boundaries are explicit
- All decisions in the decision tree are resolved (decided, deferred, or blocked)

**Alternative completion signals:** the user says "I think that's enough" or "this is helpful"; their answers become consistently confident; the conversation circles without new insight; or enough is captured for the user's stated purpose (even if the spec isn't "complete").

## Determine output format

Select based on context:

| Condition | Format | Action |
|-----------|--------|--------|
| User provided a ticket or existing doc | **Update existing artifact** | Integrate findings, mark new sections with "NEW:" prefix, preserve existing structure |
| User needs implementation-ready spec | **Standalone specification** | Use the spec template in `interview-loop.md` |
| Idea is early-stage or exploratory | **Summary for discussion** | Synthesize key insights, list open questions, skip formal structure |
| User asked "is this worth building" | **Diagnostic memo** | Lead with demand evidence, status quo, narrow wedge, risks, and assignment |
| User is diagnosing a stuck operation, queue, or bottleneck | **Constraint interview notes** | Summarize system goal, suspected constraint, evidence, local-optimum traps, next measurement, and assignment |
| User says "this is helpful" / "that's enough" | **No output needed** | The interview itself achieved the goal |

## Chain to next steps

After producing output, suggest relevant next actions:
- **Implementation ready?** → "Want me to start building this?" (chains to relevant implementation skills)
- **Needs broader input?** → "Should I write this up for team review?" (chains to `v1-stickify` for persuasive framing)
- **Ticket?** → "Want me to create/update the ticket?" (chains to whatever issue tooling the project has wired up)
- **PRD needed?** → "Should I expand this into a full PRD?" (chains to `v1-prd`)

## Reference files

- [interview-loop.md](references/interview-loop.md) — the interview mechanics: decision tree, first question and depth calibration, conducting rounds, recommended answers, uncertainty handling, question categories, and the spec template.
- [examples.md](references/examples.md) — sample interview transcript and quick reference.
