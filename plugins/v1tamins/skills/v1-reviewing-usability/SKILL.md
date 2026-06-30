---
name: v1-reviewing-usability
description: Use when reviewing a UI, product flow, prototype, form, admin surface, or control for user-error risk. Triggers on "review this UI", "usability review", "why is this confusing", "is this flow discoverable", "review this interaction".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---
# Reviewing Usability

Review an interaction for whether a real user can discover what to do, do it correctly, understand what happened, and recover when things go wrong.

Default mode is review-only. Recommend fixes, but do not edit source files unless the user explicitly asks for implementation.

## Quick Start

For a product surface, prototype, screenshot, app flow, form, dashboard interaction, admin tool, or physical/digital control:

1. Identify the user's concrete goal and starting context.
2. Inspect the actual rendered or visible surface when available; do not review only source code, alt text, or requirements if the interaction can be viewed.
3. Walk the action cycle: goal, plan, specify, perform, perceive, interpret, and compare.
4. Check discoverability, signifiers, mappings, feedback, constraints, conceptual model, and error recovery.
5. Return findings first, ordered by severity, with concrete fixes and validation checks.

## What To Review

Review every visible or implied step in the interaction:

- Controls, labels, affordances, icons, buttons, gestures, keyboard shortcuts, and disabled states.
- Entry points, empty/loading/error states, success states, confirmation states, and recovery paths.
- Form fields, validation, defaults, destructive actions, permissions, and mode switches.
- Navigation, hierarchy, object relationships, state changes, and system-generated feedback.
- Copy that explains what something is, what will happen, or what already happened.

If the surface is not visible, first try to render or open it. If rendering is blocked, say exactly what was reviewed instead.

## Review Workflow

### 1. Establish The User Task

Extract or infer:

| Field | Questions |
| --- | --- |
| User | Who is trying to do the task, and what do they already know? |
| Goal | What outcome are they trying to produce? |
| Context | What happened just before this surface appears? |
| Stakes | What happens if the user gets it wrong, gives up, or misunderstands state? |
| Success | How should the user know they are done? |

If the task is unclear, mark that as a finding before discussing layout, copy, or style.

### 2. Action-Cycle Walkthrough

Walk the interaction from the user's point of view using the shared [interaction review taxonomy](references/interaction-review-taxonomy.md). Use its action-cycle stages to find gulfs of execution and evaluation.

### 3. Discoverability Pass

Use the taxonomy's discoverability mechanisms to name the exact failure: affordance, signifier, mapping, feedback, constraint, conceptual model, or knowledge-in-the-world gap.

Do not stop at "the button should be clearer." Explain why the user would mispredict the outcome.

### 4. Error-Design Pass

Treat user mistakes as design evidence before treating them as user failure. Use the taxonomy's error modes and fix priority to separate slips, mistakes, mode errors, memory burdens, irreversible actions, automation surprises, and extreme-input failures.

### 5. Redesign Recommendations

For each actionable issue, propose the smallest change that fixes the user-task failure.

Avoid generic advice such as "make it intuitive" or "improve UX." Tie every fix to the user's goal, predicted action, observed confusion, or failure mode.

## Output Format

Use this structure unless the user asks for a different format:

```markdown
## Findings

[Severity] Surface / step - Short title
Problem: What makes the interaction hard to discover, execute, interpret, or recover from.
Impact: How this affects task success, trust, time, or error risk.
Fix: Concrete redesign.
Validation: How to verify the redesign works.
Confidence: N/5.

## What Works

- Useful strengths worth preserving.

## Action-Cycle Map

| Stage | User Expectation | Surface Signal | Risk |
| --- | --- | --- | --- |

## Redesign Sketch

- Minimal sequence of changes.

## Data Gaps

- Unavailable rendering, untested device size, missing user context, inaccessible prototype state, or assumptions.
```

Severity model:

- **Critical:** likely to cause irreversible harm, data loss, security/privacy error, money movement error, or dangerous misuse.
- **High:** blocks the primary task or causes a likely serious mistake.
- **Medium:** creates confusion, hesitation, wrong turns, or avoidable support burden.
- **Low:** polish issue with a clear readability or learnability benefit.

If no findings are found, say so and list residual risks, such as uninspected mobile state, unavailable permissions, missing analytics, or untested novice users.

## Review Checks

Before finalizing, ask:

- What does the user believe they can do from this surface?
- What action will the user try first, and why?
- What feedback confirms the action succeeded, failed, or is still pending?
- What state, scope, object, mode, or permission is invisible but necessary?
- What failure would be blamed on the user even though the interface invited it?
- What cues could be moved from memory into the world?
- Did the review inspect the rendered interaction, not just implementation or requirements?

## Chaining

- Use `v1-testing-prototypes` when the goal is to plan or synthesize live user sessions.
- Use `v1-reviewing-data-graphics` for charts, quantitative dashboards, and metric displays.
- Use `v1-debug` when the confusing interaction has already produced a production failure, support incident, or reproducible bug.
- Use `v1-prd` after the review reveals requirements, states, or edge cases that must be specified.

## When Not To Use This Skill

- Do not use for live prototype-test planning or synthesis; use `v1-testing-prototypes`.
- Do not use for chart or metrics truthfulness reviews unless the main issue is interaction; use `v1-reviewing-data-graphics`.
- Do not use for production bug root-cause work; use `v1-debug`.
- Do not use for broad product viability or customer-demand questions; use `v1-learning-from-customers` or `v1-strategy-review`.

## Examples

**Ambiguous destructive action**

Finding: A delete action appears beside multiple objects, but the confirmation does not name the selected object or recovery path.

Fix: Name the object, show the consequence, require confirmation only at the destructive boundary, and provide undo when feasible.

**Missing async feedback**

Finding: A save button returns to its idle state while the request is still pending, so users click repeatedly or navigate away.

Fix: Show pending state, disable duplicate submit, report success or failure, and preserve user input on failure.

**Poor control mapping**

Finding: A row of toggles controls a different row of settings below it, forcing users to infer which toggle affects which object.

Fix: Place each control next to the object it controls or group the controlled object and control in one repeated unit.
