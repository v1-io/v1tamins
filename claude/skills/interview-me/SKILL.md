---
name: interview-me
description: Use when the user provides an idea, feature request, Linear ticket, or concept that needs fleshing out. Triggers on "interview me about X", "help me spec out Y", "I have an idea for Z", "flesh out this idea".
---

# Interview Me

Collaboratively refine ideas through structured questioning - helping both Claude understand and the user crystallize their thinking. The interview process itself is valuable, not just the final deliverable.

## Interview Workflow

### 1. Understand the Starting Point

Read any provided context (Linear ticket, feature description, rough idea). Identify:
- What's explicitly stated vs. what's assumed
- The domain and technical context
- Who the stakeholders are

### 2. Gather Existing Context

Before interviewing, use available tools to understand what already exists:

- **Linear/Jira**: Fetch project descriptions, related issues, initiative context
- **Codebase**: Search for related code, existing implementations, architectural patterns
- **Documents**: Read related specs, PRDs, or design docs

This prevents asking questions already answered elsewhere and shows the user you've done homework.

### 3. Open with the Right First Question

The first question shapes the entire interview. Choose based on what the user provided:

| Starting Input | First Question Strategy |
|---------------|----------------------|
| Vague idea ("I want to build X") | "What's the problem you're solving, and who has it worst right now?" |
| Feature request with some detail | "What workaround are people using today, and what breaks about it?" |
| Linear ticket / spec | "What's the most uncertain part of this spec?" |
| Technical concept | "What's the simplest version of this that would be useful?" |

Avoid generic openers like "tell me more" or "what's the goal." The first question should demonstrate you understood the input and are already thinking ahead.

### 4. Conduct the Interview

Use AskUserQuestion repeatedly. Interview until sufficient understanding is reached.

**Question Strategy:**
- Ask 2-4 questions per round maximum
- Each question should unlock new understanding, not confirm obvious facts
- Progress from foundational to detailed to edge cases
- When an answer reveals complexity, drill deeper before moving on
- Use `multiSelect: true` when choices aren't mutually exclusive

**Handling Uncertainty:**

| Response Type | Meaning | Action |
|--------------|---------|--------|
| "I don't know" | Needs research | Record as **Open Question (research needed)**, move on |
| "I haven't decided" | Decision pending | Record as **Open Question (decision needed)**, note tradeoffs discussed |
| "It depends" | Conditional answer | Drill into conditions -- "What does it depend on?" |
| "I don't care" / "Either way" | Low priority for user | Make a reasonable default recommendation and note it |
| "We should ask [person]" | Blocked on stakeholder | Record as **Open Question (blocked: [person])**, move on |

Don't keep pushing when user signals uncertainty. Document it with the right label and move on.

**Adapt to Communication Style:**
- **Terse answers**: User is busy or decisive. Ask fewer, more targeted questions. Don't re-ask in different words.
- **Long, exploratory answers**: User is thinking out loud. Let them finish, then synthesize back before next question.
- **"I don't know" frequently**: Shift from probing to proposing. Offer options instead of open questions.
- **Technical depth**: Match their level. Don't oversimplify for an engineer or get technical with a PM.

**Question Categories (cycle through as needed):**

| Category | Focus | Example Non-Obvious Questions |
|----------|-------|------------------------------|
| **Current State** | What exists today | "What workaround exists now?" / "How is this problem currently handled?" |
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
- [ ] Constraints
- [ ] Users & Actors
- [ ] State & Data
- [ ] Boundaries
- [ ] Failure Modes
- [ ] Risk & Priority
- [ ] Validation
- [ ] Evolution
- [ ] Integration

Not all categories need checking -- depth calibration (step 6) determines which matter. But the checklist prevents accidentally skipping important areas.

### 5. Avoid These Question Patterns

- Don't ask what's already stated in the input
- Don't ask "what's the goal" if the goal is clear
- Don't ask binary yes/no when the interesting answer is "it depends"
- Don't ask about implementation details before understanding constraints
- Don't confirm assumptions--challenge them

### 6. Calibrate Depth

Not everything needs full specification. Ask early:
- "For this scope, are you looking for full design or initial analysis?"

Then adjust approach:
- **Full design**: Probe until implementation-ready
- **Analysis/exploration**: Stop when problem is well-characterized, solutions can be TBD
- **Mixed**: Go deep on core areas, lighter on peripheral ones

### 7. Recognize Completion

Stop interviewing when:
- Core user journeys are mapped
- Error handling and edge cases are addressed (or marked TBD appropriately)
- Integration points and dependencies are identified
- Success criteria and metrics are defined
- Scope boundaries are explicit

**Alternative Completion Signals:**
- User says "I think that's enough" or "this is helpful"
- User's answers become consistently confident (uncertainty resolved)
- Conversation is circling without new insights
- Enough captured for user's stated purpose (even if spec isn't "complete")

### 8. Synthesize Before Committing

Before writing final output:
1. Summarize key findings back to user in conversational form
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
- **Needs broader input?** -> "Should I write this up for team review?" (chains to `stickify` for persuasive framing)
- **Linear ticket?** -> "Want me to create/update the Linear ticket?" (chains to Linear MCP tools)
- **PRD needed?** -> "Should I expand this into a full PRD?" (chains to `prd` skill)

## Reference Files

- [examples.md](references/examples.md) -- Sample interview progression across 5 rounds
