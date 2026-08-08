# Domain Docs

This is a single-context repository.

## Before exploring or changing code

1. Read `CONTEXT.md` at the repository root.
2. Read ADRs under `docs/adr/` that touch the area being changed.
3. Use the vocabulary defined in `CONTEXT.md`.

If one of these files does not exist, proceed silently. Do not flag its absence
and do not propose creating it upfront. The `domain-modeling` skill creates
these lazily, when a term or a decision actually gets resolved.

## Use the glossary's vocabulary

When output names a domain concept — an issue title, a refactor proposal, a
hypothesis, a test name — use the term as `CONTEXT.md` defines it. Do not drift
to a synonym the glossary explicitly lists under `_Avoid_`.

If a needed concept is not in the glossary, that is a signal. Either the term is
being invented and the project does not use it, which is a reason to
reconsider, or there is a real gap worth recording.

## Add an ADR for durable decisions

Write or update an ADR when a durable architecture or delivery-contract decision
is made. Number them sequentially under `docs/adr/`.

## Flag ADR conflicts

If output contradicts an existing ADR, surface the conflict rather than
silently overriding it:

> Contradicts ADR-0007 (event-sourced orders), but worth reopening because…

## Do not create a context map

Do not add `CONTEXT-MAP.md` or per-context glossary files unless this
repository becomes a genuine multi-context monorepo.
