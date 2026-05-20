# Advanced Prompting Patterns

Copied and condensed from the original `v1-prompt-engineering` skill so the GPT-5.4-focused fork keeps the reusable cross-model ideas that still matter.

## Table of Contents

1. [Context window management](#context-window-management)
2. [Degrees of freedom](#degrees-of-freedom)
3. [Persuasion principles for agent prompts](#persuasion-principles-for-agent-prompts)
4. [Ethical use](#ethical-use)
5. [Quick reference](#quick-reference)

## Context window management

Treat the context window as a public good.
Your prompt competes with:

- system instructions
- conversation history
- tool metadata
- other skills or commands
- the actual task input

Default assumption: the model is already smart.
Only add context the model would not reliably infer on its own.

Use this test on every paragraph:

- Does the model really need this explanation?
- Can this be implied instead of stated?
- Does this instruction justify its token cost?

Prefer concise examples and compact reusable blocks over long prose explanations.

## Degrees of freedom

Match prompt specificity to task fragility.

### High freedom

Use when:

- multiple approaches are valid
- decisions depend on local context
- heuristics matter more than exact sequencing

Pattern:

```markdown
1. Analyze the situation
2. Identify risks and edge cases
3. Choose the best approach for the current context
4. Verify alignment with local conventions
```

### Medium freedom

Use when:

- a preferred pattern exists
- some variation is acceptable
- inputs or environment details change the implementation

Pattern:

```markdown
Use this template and adapt it as needed:

def run_task(input_data, mode="default", include_checks=True):
    ...
```

### Low freedom

Use when:

- the workflow is fragile
- order matters
- consistency matters more than adaptation
- mistakes are expensive

Pattern:

```markdown
Run exactly this command:

python scripts/migrate.py --verify --backup

Do not change flags or sequence.
```

Analogy:

- narrow bridge with cliffs = low freedom
- open field = high freedom

## Persuasion principles for agent prompts

These patterns are useful when writing commands, hooks, or agent skills that need reliable follow-through.
Use them to improve discipline and clarity, not to manipulate.

### 1. Authority

Use for bright-line rules and safety-critical requirements.

- good: `Always verify before finalizing.`
- avoid: weak suggestions for non-negotiable rules

### 2. Commitment

Use to force explicit choices or progress tracking.

- announce which path is being taken
- keep a checklist
- make decisions explicit

### 3. Scarcity

Use for timing-sensitive steps.

- `Before proceeding, run the verification step.`
- `Immediately after the edit, run the validator.`

### 4. Social proof

Use to establish norms and common failure modes.

- `Skipping verification causes misses.`
- `Coverage without tracking drops items.`

### 5. Unity

Use collaborative language when the model should act like a teammate.

- `We're trying to land a safe, minimal change.`
- `Prefer honest technical judgment over pleasing phrasing.`

### 6. Reciprocity

Use sparingly. Most prompt systems do not need it.

### 7. Liking

Avoid for compliance-heavy prompts. It can encourage flattery and reduce honesty.

## Ethical use

Legitimate uses:

- ensuring critical practices are followed
- preventing predictable failure modes
- making complex workflows easier to execute correctly

Avoid:

- guilt-based pressure
- fake urgency
- manipulation for personal gain

Use this test:
Would this still serve the user's real interests if they understood the technique being used?

## Quick reference

When designing a prompt, ask:

1. What kind of task is this?
2. How much freedom is safe?
3. Which behavior needs to change?
4. Which principle helps without oversteering?
5. Is this still concise enough to justify its token cost?
