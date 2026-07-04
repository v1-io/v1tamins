# Shared Review Skeleton

Common mechanics for v1's review-only skills — `v1-reviewing-usability` and `v1-reviewing-data-graphics`. Each keeps its own lens, severity semantics, and examples; this file holds what they share so it is maintained once. (Referenced from data-graphics as `../v1-reviewing-usability/references/review-skeleton.md`.)

## Posture

Default mode is review-only. Recommend fixes or redesigns, but do not edit source files unless the user explicitly asks for implementation.

## Inspect the real surface

Inspect the actual rendered or visible artifact when available; do not review only source code, OCR, alt text, requirements, or data tables when the rendered surface can be viewed. If rendering is blocked, say exactly what was reviewed instead.

## Return findings first

Lead with findings, ordered by severity, each with a concrete fix and a validation check. For each actionable issue, name the decision at risk, the lens category, the visible evidence, the likely cost, and the smallest fix. Avoid generic advice ("make it cleaner", "improve UX", "use better colors") — tie every fix to the decision, data, user goal, or failure mode.

## Output Format

Use this structure unless the user asks for a different format:

```markdown
## Findings

[Severity] Surface - Short title
Problem: What is wrong.
Impact: How it misleads, slows, or endangers the reader or user.
Fix: Concrete redesign.
Validation: How to verify the fix works.
Confidence: N/5.

## What Works

- Strengths worth preserving.

## Redesign Sketch

- Minimal sequence of changes.

## Data Gaps

- Missing inputs, unavailable rendering, unreadable content, or assumptions.
```

A skill may add one domain-specific section (for example, an Action-Cycle Map) — see the skill body.

## Severity Tiers

Four tiers, most-severe first: **Critical**, **High**, **Medium**, **Low**. Each skill defines what Critical and High mean in its domain. If no findings, say so and list the residual risks (uninspected states, unavailable data, assumptions).
