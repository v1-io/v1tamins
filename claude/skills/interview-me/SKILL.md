---
name: interview-me
description: Collaboratively refine ideas through structured questioning - helping both Claude understand and the user crystallize their thinking. Use when the user provides an idea, feature request, Linear ticket, or concept that needs fleshing out. Triggers on requests like "interview me about X", "help me spec out Y", "I have an idea for Z", or when explicitly invoked. Output format adapts to context (update existing artifacts, create new specs, or just synthesize insights).
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

### 3. Conduct the Interview

Use AskUserQuestion repeatedly. Interview until sufficient understanding is reached.

**Question Strategy:**
- Ask 2-4 questions per round maximum
- Each question should unlock new understanding, not confirm obvious facts
- Progress from foundational to detailed to edge cases
- When an answer reveals complexity, drill deeper before moving on
- Use `multiSelect: true` when choices aren't mutually exclusive

**Handling Partial Knowledge:**
- "TBD", "not sure", "need to explore" are valuable answers, not failures
- Capture these explicitly as Open Questions in output
- Don't keep pushing when user signals uncertainty - document it and move on
- Distinguish between "haven't decided" (decision needed) vs. "don't know yet" (research needed)

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

### 4. Avoid These Question Patterns

- Don't ask what's already stated in the input
- Don't ask "what's the goal" if the goal is clear
- Don't ask binary yes/no when the interesting answer is "it depends"
- Don't ask about implementation details before understanding constraints
- Don't confirm assumptions—challenge them

### 5. Calibrate Depth

Not everything needs full specification. Ask early:
- "For this scope, are you looking for full design or initial analysis?"

Then adjust approach:
- **Full design**: Probe until implementation-ready
- **Analysis/exploration**: Stop when problem is well-characterized, solutions can be TBD
- **Mixed**: Go deep on core areas, lighter on peripheral ones

### 6. Recognize Completion

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

### 7. Synthesize Before Committing

Before writing final output:
1. Summarize key findings back to user in conversational form
2. Highlight the most important insights and open questions
3. Confirm this matches their understanding
4. Ask if anything was missed before committing to artifact

This catches misunderstandings before they're written into permanent artifacts.

### 8. Determine Output Format

Assess what's appropriate for the situation:

- **Update existing artifact** (Linear project, doc, ticket) - Integrate findings into existing structure
- **Standalone specification** - Create new document using spec template below
- **Summary for discussion** - Synthesize key insights without formal structure
- **No output needed** - Sometimes the interview itself achieved the goal

**When updating existing artifacts:**
1. Show synthesis to user before committing
2. Clearly mark new sections (e.g., "NEW:" prefix)
3. Preserve existing structure, add rather than replace
4. Update related sections for consistency

### 9. Produce the Specification (when appropriate)

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

## Example Interview Progression

**Round 1 - Current State & Foundational:**
- "What workaround are people using today?"
- "Who is the primary user, and what's their mental model coming into this?"
- "What's the cost of getting this wrong vs. shipping slowly?"

**Round 2 - Constraints & Depth Calibration:**
- "What technical constraints from the existing system affect this?"
- "For this project scope, are you looking for full design or initial analysis?"
- "What's the minimum viable version vs. the full vision?"

**Round 3 - Integration & Risk:**
- "How does this interact with [specific related feature]?"
- "If this work isn't done, what breaks first? Rank by impact."
- "Who needs to be notified and when?"

**Round 4 - Edge Cases & Validation:**
- "What happens with concurrent operations?"
- "What's the smallest experiment to validate this approach?"
- "How do we handle the 'undo' scenario?"

**Round 5 - Evolution & Wrap-up:**
- "What's the migration story for existing data/users?"
- "What are we intentionally deferring?"
- "Is there anything we haven't covered that should be captured?"
