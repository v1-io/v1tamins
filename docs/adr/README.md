# Architecture Decision Records

One file per durable decision, numbered sequentially:
`0001-short-kebab-case-title.md`.

Write an ADR when a decision is expensive to reverse and a future reader would
otherwise have to reconstruct the reasoning: an architecture choice, a delivery
contract, a data model boundary, a dependency the project now depends on.

Do not write one for a routine implementation choice.

## Template

```markdown
# ADR-0001: <decision in a short noun phrase>

- Status: proposed | accepted | superseded by ADR-0009
- Date: YYYY-MM-DD

## Context

What forced a decision. The constraints that were real at the time.

## Decision

What was chosen, stated in the active voice.

## Consequences

What this makes easy, what it makes hard, and what it rules out.
```

Supersede rather than edit. When a decision changes, write a new ADR and mark
the old one superseded so the history stays readable.
