---
name: v1-interview-me
description: Use when the user provides an idea, feature request, Linear ticket, or concept that needs fleshing out, product validation, or office-hours-style questioning. Triggers on "interview me about X", "help me spec out Y", "I have an idea for Z", "flesh out this idea", "office hours", "is this worth building".
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
- Claude Code: `/v1-interview-me [LINEAR_TICKET_ID or idea]`
- Codex: invoke `v1-interview-me` from the skills menu or use `$v1-interview-me [LINEAR_TICKET_ID or idea]`

Examples:
```text
/v1-interview-me
/v1-interview-me <LINEAR_TICKET_ID>
/v1-interview-me <paste idea or feature description>
```

In Codex, the slash examples below map directly to `$v1-interview-me ...`.

Can also be triggered conversationally: "I have an idea for X", "help me spec out Y", "flesh out this concept".

## Interview Workflow

### 1. Understand the Starting Point

Read any provided context (Linear ticket, feature description, rough idea). Identify:
- What's explicitly stated vs. what's assumed
- The domain and technical context
- Who the stakeholders are

### 2. Gather Existing Context

Before interviewing, explore what already exists using available tools:

- **Linear/Jira**: Fetch project descriptions, related issues, initiative context
- **Codebase**: Search for related code, existing implementations, architectural patterns
- **Documents**: Read related specs, PRDs, or design docs

**Hard rule: if a question can be answered by exploring the codebase, Linear, or documents -- explore instead of asking.** Only interview for things that require the user's judgment, intent, or domain knowledge. Don't waste interview rounds on things you can look up.

### 2.5 Choose the Interview Posture

Classify the session before asking the first question:

| Posture | Use When | Interview Bias |
|---------|----------|----------------|
| **Startup diagnostic** | Customer, revenue, fundraising, market, internal sponsor, adoption, or "worth building" language appears | Demand evidence, status quo, narrow wedge, observation, future fit |
| **Builder exploration** | Side project, learning, hackathon, open source, creative tool, or "cool thing" language appears | Delight, fastest demo, who to show, surprising combinations, next build step |
| **Implementation spec** | User already knows this should be built | Decisions, constraints, edge cases, integration, validation |

Default to **Startup diagnostic** when the user asks whether something is worth building. Default to **Builder exploration** when the user wants to riff before committing. Switch postures mid-interview if the user's answers reveal a different job.

**Startup diagnostic forcing questions:**
- What's the strongest evidence someone actually wants this, not just finds it interesting?
- What are people doing right now instead, and what does that workaround cost?
- Who needs this most? Name the role, trigger, and consequence.
- What's the smallest version someone would pay for or adopt this week?
- Have you watched someone try to solve this without guiding them? What surprised you?
- If the world changes over the next 3 years, does this become more necessary or less?

Ask these one at a time only when the answer is not already clear. Push vague answers once with a concrete follow-up, then record the gap and move on.

**Builder exploration prompts:**
- What's the version you would be excited to show someone this week?
- What would make the first demo feel surprisingly good?
- What's the fastest path to something usable?
- What existing thing is closest, and what should be different?
- What would the 10x version include if time were free?

End every posture with one concrete assignment: the next thing the user or agent should do.

### 3. Map the Decision Tree

After gathering context, identify the major decisions and branches in the design. List them explicitly:

> "I see these key decisions that need resolving: A, B, C..."

Walk dependencies in order -- resolve upstream decisions before probing downstream ones. A decision is "resolved" when it reaches one of these states:

| State | Example |
|-------|---------|
| **Decided** | "We'll use webhooks, not polling" |
| **Intentionally deferred** | "We'll decide the retry strategy after load testing" |
| **Blocked on external input** | "Need pricing info from the vendor before choosing" |

**Branch closure rule**: don't move on from a decision until it reaches one of these states. This prevents the interview from producing a spec full of implicit assumptions.

### 4. Open with the Right First Question

The first question shapes the entire interview. Choose based on what the user provided:

| Starting Input | First Question Strategy |
|---------------|----------------------|
| Vague idea ("I want to build X") | "What's the problem you're solving, and who has it worst right now?" |
| Feature request with some detail | "What workaround are people using today, and what breaks about it?" |
| Linear ticket / spec | "What's the most uncertain part of this spec?" |
| Technical concept | "What's the simplest version of this that would be useful?" |

Avoid generic openers like "tell me more" or "what's the goal." The first question should demonstrate you understood the input and are already thinking ahead.

**In the same opening round, calibrate depth:**
- "Are you looking for a full spec, or more of an initial analysis to decide if this is worth pursuing?"

Then adjust the rest of the interview:
- **Full design**: Probe until implementation-ready. Cover all relevant question categories.
- **Analysis/exploration**: Stop when problem is well-characterized, solutions can be TBD. Focus on Current State, Constraints, Risk & Priority.
- **Mixed**: Go deep on core areas, lighter on peripheral ones.

### 5. Conduct the Interview

Use AskUserQuestion repeatedly. Interview until sufficient understanding is reached.

**Question Strategy:**
- Ask 2-4 questions per round maximum
- Each question should unlock new understanding, not confirm obvious facts
- Progress from foundational to detailed to edge cases
- When an answer reveals complexity, drill deeper before moving on
- Use `multiSelect: true` when choices aren't mutually exclusive

**Progressive Synthesis:**

After every 2-3 rounds, share a brief summary of your current understanding:

> "Here's what I'm hearing so far: [2-4 sentence synthesis]. Before I go deeper on X, does this track?"

- Frame as a checkpoint, not a conclusion
- If the user corrects the summary, acknowledge and adjust before continuing
- Keep these lightweight -- conversational, not a slide deck
- This catches drift early instead of discovering misalignment at the end

**Handling Uncertainty:**

| Response Type | Meaning | Action |
|--------------|---------|--------|
| "I don't know" | Needs research | Record as **Open Question (research needed)**, move on |
| "I haven't decided" | Decision pending | Record as **Open Question (decision needed)**, note tradeoffs discussed |
| "It depends" | Conditional answer | Drill into conditions -- "What does it depend on?" Get the conditions enumerated. |
| "I don't care" / "Either way" | Low priority for user | Make a reasonable default recommendation and note it |
| "We should ask [person]" | Blocked on stakeholder | Record as **Open Question (blocked: [person])**, move on |

Don't keep pushing when user signals uncertainty. Document it with the right label and move on.

**Adapt to Communication Style:**
- **Terse answers**: User is busy or decisive. Ask fewer, more targeted questions. Don't re-ask in different words.
- **Long, exploratory answers**: User is thinking out loud. Let them finish, then synthesize back before next question.
- **"I don't know" frequently**: Shift from probing to proposing. Offer options instead of open questions.
- **Technical depth**: Match their level. Don't oversimplify for an engineer or get technical with a PM.

**Constructive Challenge:**

Actively probe for weak spots in the plan:
- Expose weak defaults, conflicting assumptions, and irreversible choices
- Surface flawed assumptions as questions: "I notice X assumes Y, but earlier you said Z -- how do those fit together?"
- Name obvious gaps once, clearly: "One thing worth addressing: [gap]. Intentional or something to work through?"
- Push on "it depends" -- get the conditions enumerated rather than leaving them vague
- Don't repeatedly challenge the same point. State once, record the user's response, move on.

**Recognizing Pivots:**

If answers consistently point away from the original idea (the real problem is different, the assumed user is wrong, a simpler solution exists), pause and name it:

> "Based on what you've described, it sounds like the core problem might actually be X rather than Y. Should we shift the interview in that direction?"

Don't silently drift. Explicitly acknowledge the pivot so the user can agree or disagree. If they agree, restart progressive synthesis from the new framing. If they disagree, note the alternative framing as an open question.

**Question Categories (cycle through as needed):**

| Category | Focus | Example Non-Obvious Questions |
|----------|-------|------------------------------|
| **Current State** | What exists today | "What workaround exists now?" / "How is this problem currently handled?" |
| **Demand & Wedge** | Whether the idea has real pull and a narrow entry point | "Who would be upset if this disappeared?" / "What's the smallest version worth adopting this week?" |
| **Constraints** | What limits the solution space | "What's the recovery story if this fails mid-operation?" / "What existing system invariants must we preserve?" |
| **Users & Actors** | Who interacts and how | "Who has to clean up when this goes wrong?" / "What's the worst thing a confused user could do here?" |
| **State & Data** | What changes and persists | "What happens to in-flight data if this is deployed mid-operation?" / "What's the source of truth when systems disagree?" |
| **Boundaries** | Where responsibility ends | "What's explicitly NOT in scope that someone might assume is?" / "At what scale does this approach break down?" |
| **Failure Modes** | What breaks and how | "What's the blast radius if the dependency is down for an hour?" / "How do we know this is broken before users tell us?" |
| **Risk & Priority** | What matters most | "If this work isn't done, what breaks first?" / "Rank these concerns by impact" |
| **Validation** | How to verify | "What's the smallest experiment to test this hypothesis?" / "How would we know this worked?" |
| **Evolution** | How it changes over time | "What's the migration path when requirements change?" / "What decision here will be hardest to reverse?" |
| **Integration** | How it connects | "What existing workflows does this interrupt or complicate?" / "Who needs to know when this happens?" |

**Category Coverage Tracker:**
- [ ] Current State
- [ ] Demand & Wedge
- [ ] Constraints
- [ ] Users & Actors
- [ ] State & Data
- [ ] Boundaries
- [ ] Failure Modes
- [ ] Risk & Priority
- [ ] Validation
- [ ] Evolution
- [ ] Integration

Not all categories apply -- depth calibration from step 4 determines which matter. For analysis scope, focus on Current State, Constraints, Risk & Priority. For full design, cover all relevant categories.

### 6. Avoid These Question Patterns

- Don't ask what's already stated in the input
- Don't ask "what's the goal" if the goal is clear
- Don't ask binary yes/no when the interesting answer is "it depends"
- Don't ask about implementation details before understanding constraints
- Don't confirm assumptions--challenge them

### 7. Recognize Completion

Stop interviewing when:
- Core user journeys are mapped
- Error handling and edge cases are addressed (or marked TBD appropriately)
- Integration points and dependencies are identified
- Success criteria and metrics are defined
- Scope boundaries are explicit
- All decisions in the decision tree are resolved (decided, deferred, or blocked)

**Alternative Completion Signals:**
- User says "I think that's enough" or "this is helpful"
- User's answers become consistently confident (uncertainty resolved)
- Conversation is circling without new insights
- Enough captured for user's stated purpose (even if spec isn't "complete")

### 8. Synthesize Before Committing

Before writing final output:
1. Summarize the full picture, incorporating any corrections from earlier progressive check-ins
2. Highlight the most important insights and open questions
3. Confirm this matches their understanding
4. Ask if anything was missed before committing to artifact

This catches misunderstandings before they're written into permanent artifacts.

### 9. Determine Output Format

Select based on context:

| Condition | Format | Action |
|-----------|--------|--------|
| User provided a Linear ticket or existing doc | **Update existing artifact** | Integrate findings, mark new sections with "NEW:" prefix, preserve existing structure |
| User needs implementation-ready spec | **Standalone specification** | Use spec template in step 10 |
| Idea is early-stage or exploratory | **Summary for discussion** | Synthesize key insights, list open questions, skip formal structure |
| User asked "is this worth building" | **Diagnostic memo** | Lead with demand evidence, status quo, narrow wedge, risks, and assignment |
| User says "this is helpful" / "that's enough" | **No output needed** | The interview itself achieved the goal |

### 10. Produce the Specification (when appropriate)

For standalone specs, use this structure:

```markdown
# [Feature/Concept Name] Specification

## Overview
[1-2 paragraph summary of what this is and why it matters]

## Goals & Non-Goals
**Goals:**
- [Explicit objectives]

**Non-Goals:**
- [What this explicitly does NOT do]

## User Stories / Use Cases
[Primary flows with actor, action, outcome]

## Demand Evidence
[Specific behaviors, status quo, and narrowest wedge]

## Technical Design
[Architecture, data flow, key decisions]

## Edge Cases & Error Handling
[What happens when things go wrong]

## Dependencies & Integration Points
[What this touches and relies on]

## Open Questions
[Anything that still needs resolution - including intentional TBDs]

## Success Criteria
[How we know this works]
```

### 11. Chain to Next Steps

After producing output, suggest relevant next actions:
- **Implementation ready?** -> "Want me to start building this?" (chains to relevant implementation skills)
- **Needs broader input?** -> "Should I write this up for team review?" (chains to `v1-stickify` for persuasive framing)
- **Linear ticket?** -> "Want me to create/update the Linear ticket?" (chains to whatever Linear tooling the project has wired up)
- **PRD needed?** -> "Should I expand this into a full PRD?" (chains to `v1-prd` skill)

## Reference Files

- [examples.md](references/examples.md) -- Sample interview transcript and quick reference
