---
name: v1-stickify
description: Use when making communication copy more memorable or persuasive. Triggers on "stickify", "make this memorable", or "improve this pitch".
---
# Stickify

Apply the SUCCESs framework from *Made to Stick* (Chip Heath & Dan Heath) to make communications memorable, understandable, and actionable.

## Quick Start

Typical invocations:
- Claude Code: `/v1-stickify [paste existing copy here]`
- Codex: invoke `v1-stickify` from the skills menu or use `$v1-stickify [paste existing copy here]`

Or describe what you need: "Write a landing page headline for our AI code review tool that targets senior engineers."

## When to Use

Invoke this skill in three situations:

1. **Improve existing copy** -- user provides text and wants it stickified
2. **Write from a brief** -- user describes what they need, produce sticky copy from scratch
3. **Proactively** -- when producing any copy that would benefit from stickiness (landing pages, pitches, announcements, taglines, product descriptions, emails to customers, investor updates, team comms)

## The SUCCESs Framework

Six traits of sticky ideas:

### 1. SIMPLE -- Find the Core
Strip to the single most important thing. Forced prioritization, not dumbing down.
- Commander's Intent: "If we do nothing else, we must ___"
- If you say three things, you say nothing
- Lead with the core (don't bury the lead)
- Simple = core + compact. Proverbs over mission statements.
- Tap existing schemas: analogies, high concepts ("Jaws on a spaceship")

### 2. UNEXPECTED -- Get and Keep Attention
Break the guessing machine, then open knowledge gaps.
- **Get attention:** violate expectations, break schemas
- **Keep attention:** create curiosity gaps, pose questions, build mystery
- Surprise must be "postdictable" -- makes sense in retrospect
- Shift from "What do I convey?" to "What questions do I want them to ask?"

### 3. CONCRETE -- Make It Real
Explain in terms of human actions and sensory information.
- Replace abstractions with specific, tangible images
- Concrete props beat abstract descriptions (the leather portfolio, the bag of salt and sugar)
- Velcro theory: more sensory hooks = stickier memory
- Two people reading the same message should picture the same thing

### 4. CREDIBLE -- Make It Believable
Help people test the idea for themselves.
- Anti-authorities (real people with lived experience) can beat experts
- Vivid, specific details boost believability even when logically irrelevant
- Human-scale statistics ("one soft drink a month would double our aid to Africa")
- Sinatra Test: one example so strong it proves everything
- Testable credentials: let the audience verify it themselves

### 5. EMOTIONAL -- Make Them Care
Make people feel something for a person, not an abstraction.
- WIIFY: What's In It For You
- One person > millions (Mother Teresa principle)
- Appeal to identity ("Don't mess with Texas")
- Avoid semantic stretch -- find fresh emotional territory
- Move up Maslow's hierarchy beyond base self-interest

### 6. STORIES -- Drive Action
Stories are mental flight simulators -- simulation (how to act) + inspiration (motivation to act).
- **Challenge Plot:** overcome obstacles (David vs. Goliath)
- **Connection Plot:** bridge gaps between people (Good Samaritan)
- **Creativity Plot:** mental breakthrough, new way of seeing (Newton's apple)
- Spot stories in the wild rather than manufacturing them

## The Villain: Curse of Knowledge

The #1 enemy. Once you know something, you cannot imagine not knowing it. Tappers hear the song; listeners hear bizarre Morse code. The SUCCESs framework is the antidote.

Signs: jargon without realizing it, skipping "why this matters," burying the lead under context.

## Workflow

### When given existing text to improve

1. **Score** -- assess each SUCCESs principle:

```
| Principle  | Score | Notes |
|------------|-------|-------|
| Simple     |       |       |
| Unexpected |       |       |
| Concrete   |       |       |
| Credible   |       |       |
| Emotional  |       |       |
| Story      |       |       |
```
Score: X = strong, ~ = partial, - = absent

2. **Diagnose** -- identify the 2-3 biggest weaknesses and explain why they matter for this specific piece. Check for Curse of Knowledge symptoms.

3. **Rewrite** -- produce the improved version, making actual edits. Apply SUCCESs techniques to address each weakness. Do not just suggest changes -- make them.

4. **Diff** -- present the changes as a clear before/after diff showing exactly what changed and why:

```
BEFORE: [original passage]
AFTER:  [rewritten passage]
WHY:    [which SUCCESs principle this addresses and the specific technique used]
```

Show one diff block per significant change. Group minor wording tweaks together.

5. **Summary** -- brief recap: what the core message is, what changed, and the updated scorecard.

### When writing from a brief

1. Clarify the core message -- force prioritization. Ask if unclear: "What is the single most important thing?"
2. Identify the audience and what they already know/believe (to find schemas to tap and schemas to break)
3. Draft applying all six principles
4. Self-score against the checklist
5. Present the draft with a scorecard and rationale for key choices

### When invoked proactively

Apply the framework as an internal lens. Do not necessarily output the full scorecard -- just produce stickier copy. Bias toward concrete, unexpected, simple. Check for Curse of Knowledge before finalizing.

## Guidelines

- Not every message needs all six. But the best ones hit most.
- Start with Simple. If the core isn't clear, nothing else matters.
- Concrete is the easiest to improve and often the most impactful.
- Don't confuse sticky with dumbed down. Proverbs are simple AND profound.
- Avoid gimmicky surprise -- unexpectedness must serve the core message.
- When in doubt, make it more concrete and less abstract.

## Example

**Input:** "Our platform leverages AI to optimize developer workflows and increase productivity."

**Score:**

| Principle  | Score | Notes |
|------------|-------|-------|
| Simple     | ~     | Core buried under jargon |
| Unexpected | -     | Nothing breaks expectations |
| Concrete   | -     | "Leverages," "optimize," "workflows" -- all abstract |
| Credible   | -     | No proof, no testable claim |
| Emotional  | -     | No WIIFY, no identity appeal |
| Story      | -     | No narrative |

**Rewrite:**

```
BEFORE: Our platform leverages AI to optimize developer workflows and increase productivity.
AFTER:  Ship your PR in 10 minutes, not 2 hours. AI catches the bugs before your reviewer does.
WHY:    Concrete (specific time, specific action), Unexpected (AI as faster reviewer),
        Credible (testable claim), Emotional (WIIFY -- get your time back)
```

## Reference Files

- **references/success-framework.md** -- Deep-dive on each principle with extended examples from the book
