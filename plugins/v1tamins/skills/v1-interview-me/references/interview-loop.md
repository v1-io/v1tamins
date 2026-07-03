# Interview Loop

The mechanics of a structured interview. `SKILL.md` owns posture classification,
completion, and output format; this file owns the loop those postures drive.
Walk it in order, one focused round at a time.

## 1. Understand the starting point

Read any provided context (ticket, feature description, rough idea). Identify
what's explicitly stated vs. assumed, the domain and technical context, and who
the stakeholders are.

## 2. Gather existing context before asking

Explore what already exists using available tools: ticket/issue trackers,
codebase, related specs and docs.

**Hard rule: if a question can be answered by exploring the codebase, the issue
tracker, or documents — explore instead of asking.** Only interview for things
that require the user's judgment, intent, or domain knowledge. Don't spend
interview rounds on what you can look up.

## 3. Map the decision tree

Identify the major decisions and branches, and list them explicitly:

> "I see these key decisions that need resolving: A, B, C..."

Walk dependencies in order — resolve upstream decisions before probing
downstream ones. A decision is resolved when it reaches one of these states:

| State | Example |
|-------|---------|
| **Decided** | "We'll use webhooks, not polling" |
| **Intentionally deferred** | "We'll decide the retry strategy after load testing" |
| **Blocked on external input** | "Need pricing info from the vendor before choosing" |

**Branch closure rule:** don't move on from a decision until it reaches one of
these states. This prevents a spec full of implicit assumptions.

## 4. Open with the right first question

The first question shapes the interview. Choose based on what the user provided:

| Starting input | First-question strategy |
|---------------|----------------------|
| Vague idea ("I want to build X") | "What's the problem you're solving, and who has it worst right now?" |
| Feature request with some detail | "What workaround are people using today, and what breaks about it?" |
| Ticket / spec | "What's the most uncertain part of this spec?" |
| Technical concept | "What's the simplest version of this that would be useful?" |
| Operational bottleneck or process failure | "Where does work pile up or wait before the outcome is delivered?" |

Avoid generic openers ("tell me more", "what's the goal"). The first question
should show you understood the input and are already thinking ahead.

**In the same opening round, calibrate depth:**
- "Are you looking for a full spec, or an initial analysis to decide if this is worth pursuing?"

Then adjust the rest of the interview:
- **Full design:** probe until implementation-ready; cover all relevant categories.
- **Analysis/exploration:** stop when the problem is well-characterized; solutions can be TBD. Focus on Current State, Constraints, Risk & Priority.
- **Mixed:** go deep on core areas, lighter on peripheral ones.

## 5. Conduct the interview

Use AskUserQuestion repeatedly. Interview until sufficient understanding is reached.

**Attach a recommended answer to every question.** Use AskUserQuestion with your
proposed answer as the first option, labeled `(Recommended)`, so the user reacts
to a concrete proposal instead of facing a blank prompt. Derive the
recommendation from the context you gathered and the decision's most likely
resolution; a good recommendation is often accepted with one word, and a wrong
one gets corrected faster than an open question gets answered. When you genuinely
have no lean, say so and offer balanced options rather than a hollow "recommended"
pick. This is the loop's default questioning shape — not an occasional flourish.

**Question strategy:**
- Ask 2-4 questions per round maximum. AskUserQuestion renders each as its own card, so a small batch reads as distinct choices, not a wall of prompts.
- Each question should unlock new understanding, not confirm obvious facts.
- Progress from foundational to detailed to edge cases.
- When an answer reveals complexity, drill deeper before moving on.
- Use `multiSelect: true` when choices aren't mutually exclusive.

**Progressive synthesis.** After every 2-3 rounds, share a brief summary of your
current understanding:

> "Here's what I'm hearing so far: [2-4 sentence synthesis]. Before I go deeper on X, does this track?"

Frame it as a checkpoint, not a conclusion. If the user corrects it, acknowledge
and adjust before continuing. Keep it conversational. This catches drift early
instead of at the end.

**Handling uncertainty:**

| Response type | Meaning | Action |
|--------------|---------|--------|
| "I don't know" | Needs research | Record as **Open Question (research needed)**, move on |
| "I haven't decided" | Decision pending | Record as **Open Question (decision needed)**, note tradeoffs discussed |
| "It depends" | Conditional answer | Drill into conditions — "What does it depend on?" Enumerate them. |
| "I don't care" / "Either way" | Low priority for user | Make a reasonable default recommendation and note it |
| "We should ask [person]" | Blocked on stakeholder | Record as **Open Question (blocked: [person])**, move on |

Don't keep pushing when the user signals uncertainty. Document it with the right
label and move on.

**Adapt to communication style:**
- **Terse answers:** user is busy or decisive. Ask fewer, more targeted questions. Don't re-ask in different words.
- **Long, exploratory answers:** user is thinking out loud. Let them finish, then synthesize back before the next question.
- **"I don't know" frequently:** shift from probing to proposing. Lean harder on recommended answers and offer options instead of open questions.
- **Technical depth:** match their level. Don't oversimplify for an engineer or get technical with a PM.

**Constructive challenge.** Actively probe for weak spots:
- Expose weak defaults, conflicting assumptions, and irreversible choices.
- Surface flawed assumptions as questions: "I notice X assumes Y, but earlier you said Z — how do those fit?"
- Name obvious gaps once, clearly: "One thing worth addressing: [gap]. Intentional or something to work through?"
- Push on "it depends" — get the conditions enumerated.
- Don't repeatedly challenge the same point. State once, record the response, move on.

**Recognizing pivots.** If answers consistently point away from the original
idea (the real problem is different, the assumed user is wrong, a simpler
solution exists), pause and name it:

> "Based on what you've described, the core problem might actually be X rather than Y. Should we shift the interview in that direction?"

Don't silently drift. If they agree, restart progressive synthesis from the new
framing. If they disagree, note the alternative framing as an open question.

## 6. Question categories (cycle through as needed)

| Category | Focus | Example non-obvious questions |
|----------|-------|------------------------------|
| **Current State** | What exists today | "What workaround exists now?" / "How is this handled today?" |
| **Demand & Wedge** | Whether the idea has real pull and a narrow entry point | "What evidence do we already have?" / "Which uncertainty should customer learning resolve next?" |
| **Throughput & Constraint** | Whether this should become a constraint diagnosis | "What system is stuck?" / "What symptom makes you suspect a bottleneck?" |
| **Constraints** | What limits the solution space | "What's the recovery story if this fails mid-operation?" / "What system invariants must we preserve?" |
| **Users & Actors** | Who interacts and how | "Who cleans up when this goes wrong?" / "What's the worst thing a confused user could do?" |
| **State & Data** | What changes and persists | "What happens to in-flight data if this deploys mid-operation?" / "What's the source of truth when systems disagree?" |
| **Boundaries** | Where responsibility ends | "What's explicitly NOT in scope that someone might assume is?" / "At what scale does this break down?" |
| **Failure Modes** | What breaks and how | "What's the blast radius if the dependency is down for an hour?" / "How do we know it's broken before users tell us?" |
| **Risk & Priority** | What matters most | "If this isn't done, what breaks first?" / "Rank these concerns by impact." |
| **Validation** | How to verify | "What's the smallest experiment to test this hypothesis?" / "How would we know this worked?" |
| **Evolution** | How it changes over time | "What's the migration path when requirements change?" / "What decision here is hardest to reverse?" |
| **Integration** | How it connects | "What existing workflows does this interrupt?" / "Who needs to know when this happens?" |

**Coverage tracker** — not all categories apply; depth calibration (step 4)
decides which matter. For analysis scope, focus on Current State, Constraints,
Risk & Priority. For full design, cover all relevant categories.

- [ ] Current State
- [ ] Demand & Wedge
- [ ] Throughput & Constraint
- [ ] Constraints
- [ ] Users & Actors
- [ ] State & Data
- [ ] Boundaries
- [ ] Failure Modes
- [ ] Risk & Priority
- [ ] Validation
- [ ] Evolution
- [ ] Integration

When the interview turns into customer discovery, prototype testing, constraint
diagnosis, or PRD writing, switch skills instead of embedding that specialist
workflow here.

## 7. Avoid these question patterns

- Don't ask what's already stated in the input.
- Don't ask "what's the goal" when the goal is clear.
- Don't ask binary yes/no when the interesting answer is "it depends".
- Don't ask about implementation details before understanding constraints.
- Don't confirm assumptions — challenge them.

## 8. Synthesize before committing

Before writing any final output:
1. Summarize the full picture, incorporating corrections from earlier check-ins.
2. Highlight the most important insights and open questions.
3. Confirm this matches their understanding.
4. Ask if anything was missed before committing to an artifact.

This catches misunderstandings before they're written into permanent artifacts.

## Specification template

For standalone specs (see the output-format table in `SKILL.md`):

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
[Anything that still needs resolution — including intentional TBDs]

## Success Criteria
[How we know this works]
```
