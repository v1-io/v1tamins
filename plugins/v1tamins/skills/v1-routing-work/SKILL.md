---
name: v1-routing-work
description: Use when deciding which agent work mode fits an ambiguous task, handoff, backlog item, saved idea, or evolving product/engineering role. Triggers on "what mode is this", "route this work", "prototype or build", "builder or maintainer", "how should an agent handle this".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - AskUserQuestion
---
# Routing Work

Choose the right mode for ambiguous agent-assisted product and engineering work before the agent starts doing the wrong kind of job.

Use this skill when the request mixes invention, implementation, cleanup, growth, and operations, or when the user asks what kind of work an idea really is.

## Quick Start

1. Read the request, source material, ticket, plan, or saved item.
2. State the desired outcome in one sentence.
3. Choose one primary work mode from the table.
4. Name any secondary mode only as a later handoff, not as simultaneous scope.
5. Return a mode card with the next skill, prompt, or validation step.

## Work Modes

| Mode | Use When | Primary Output | Handoff Trigger | Common Next Skill |
| --- | --- | --- | --- | --- |
| **Prototype** | The idea, user, or shape is still unclear | Options, throwaway demo, spike, prompt pattern, or storyboard | One promising direction has enough evidence to harden | `v1-interview-me`, `v1-html-it`, `v1-testing-prototypes` |
| **Build** | The desired behavior is clear enough to make production-grade | Implementation plan, focused diff, tests, and integration path | The feature works against acceptance evidence | `v1-prd`, `v1-write-tests`, `v1-debug` |
| **Sweep** | The thing works but is messy, slow, confusing, or overbuilt | Simplification, deletion, polish, performance pass, or UX cleanup | Complexity, friction, or waste is measurably lower | `v1-simplify`, `v1-deslop`, `v1-refactor` |
| **Grow** | A shipped thing needs adoption, product-market evidence, or iteration | Learning loop, experiment, customer synthesis, or iteration plan | The next change is backed by observed user behavior | `v1-learning-from-customers`, `v1-reviewing-usability`, `v1-testing-prototypes` |
| **Maintain** | A mature surface needs reliability, security, cost, speed, or operational care | Regression fix, monitoring gap, runbook, hardening plan, or maintenance diff | The system has clearer ownership and lower operational risk | `v1-debug`, `v1-code-review`, `v1-docs-freshness` |

## Routing Rules

- Default to **Prototype** when the request is mostly idea energy, unclear audience, missing acceptance evidence, or a saved item that has not been translated into a concrete artifact.
- Default to **Build** only when the requested behavior, constraints, and validation signal are clear enough to make production choices.
- Default to **Sweep** when the current artifact exists and the main risk is needless complexity, awkward UX, performance drag, or overgrown scope.
- Default to **Grow** when the product exists and the next question is adoption, positioning, user pull, retention, or iteration based on evidence.
- Default to **Maintain** when the dominant concern is reliability, security, scalability, cost, ownership, or regression prevention.
- Do not blend modes just because all of them sound useful. If the first mode changes the evidence needed for the next mode, sequence them.
- Treat "prototype then build" as two jobs with a handoff trigger. Do not ask one pass to both explore freely and produce production-grade code.
- Ask before switching from read-only routing into irreversible edits, external mutations, or broad implementation.

## Output Format

```markdown
## Work Route

Outcome: [one sentence]
Primary mode: [Prototype / Build / Sweep / Grow / Maintain]

Why this mode:
- [evidence from the request or source]

Do now:
- [the smallest useful next action]

Do not do yet:
- [tempting mode-mixing or premature work to avoid]

Handoff trigger:
- [observable condition that allows the next mode]

Recommended next step:
- [skill, prompt, command, or artifact]

Validation:
- [how to prove this route was useful]
```

## Examples

### Saved Idea

Input: A saved post argues that product, design, data, and engineering work are merging into new agent-era roles, and asks for something reusable.

Route:

```markdown
## Work Route

Outcome: Turn the saved idea into one reusable artifact that helps agents choose the right kind of work.
Primary mode: Prototype

Why this mode:
- The source is a conceptual model, not an implementation-ready feature.
- The smallest useful artifact is a prompt or skill pattern that can be tried before reorganizing a workflow.

Do now:
- Create a narrow routing prompt or skill that distinguishes exploration, production build, cleanup, growth, and maintenance work.

Do not do yet:
- Do not redesign team roles, rename every workflow, or implement broad automation around the model.

Handoff trigger:
- The routing artifact has been used on real tasks and produces clearer next actions than the original undifferentiated request.

Recommended next step:
- Use `v1-skilling-it` if the artifact should become a shared skill, or `v1-prompt-engineering` if it should stay a prompt.

Validation:
- Run the repo's native skill validation and test the route against at least one real ambiguous task.
```

### Working But Bloated Diff

Input: A branch passes tests, but the diff added extra fallback paths, unused helpers, and verbose comments.

Route:

```markdown
## Work Route

Outcome: Make the working branch easier to maintain before it ships.
Primary mode: Sweep

Why this mode:
- The behavior already works.
- The main risk is complexity entering the codebase.

Do now:
- Run a simplification pass focused on deletion, clearer control flow, and removing unused abstractions.

Do not do yet:
- Do not add new feature scope or switch into growth experiments.

Handoff trigger:
- Tests and lint still pass after the diff is smaller and easier to review.

Recommended next step:
- Use `v1-simplify`, then `v1-code-review`.

Validation:
- Compare diff size, changed abstractions, and test output before and after the sweep.
```
