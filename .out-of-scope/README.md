# Out of Scope

Rejected skill ideas and design directions for v1tamins, recorded once with a
durable reason so they are not re-proposed and re-litigated. **Before proposing
a new skill or a structural change, check here for a matching prior rejection.**

This is a contributor-facing record at the repo root — it is not part of the
distributed plugin under `plugins/v1tamins/`.

## What goes here

One markdown file per rejected **concept** — not per request or issue. Name the
file for the concept in kebab-case (for example `no-per-skill-config-files.md`).
Match new proposals to existing files by concept, not by exact wording ("a
settings file for each skill" matches `no-per-skill-config-files.md`).

Each file states:

- **Decision** — what was rejected, in one line.
- **Why** — a durable reason: a scope or philosophy boundary, a technical
  constraint, or a strategic choice.
- **Prior requests** — a running list of times the concept came up, so repeat
  proposals are visible.

## Two rules that keep this trustworthy

1. **Deferral is not rejection.** Only record directions turned down on the
   merits. Something worth doing "later, when there's time" is a backlog item,
   not an out-of-scope entry — "too busy right now" is never a valid reason
   here. Mixing deferrals in makes the record lie.
2. **Never record an already-implemented request.** Only genuine rejections
   belong here. If a request was accepted and shipped, it is not out of scope;
   recording it would cause false "we rejected that" matches against future
   proposals.

## When a new request matches an existing entry

The maintainer decides:

- **Confirm** — same concept, still rejected: append the new mention to the
  entry's Prior requests list.
- **Reconsider** — circumstances changed: update or delete the file, then
  proceed with the work.
- **Disagree** — related but genuinely distinct: proceed; the old entry stands
  unchanged.

## Entry template

```markdown
# <Concept name>

**Decision:** <one line — what is rejected>

**Why:** <durable reason: scope/philosophy boundary | technical constraint | strategic choice>

## Prior requests
- <YYYY-MM-DD> — <where it came up> — <one line of context>
```
