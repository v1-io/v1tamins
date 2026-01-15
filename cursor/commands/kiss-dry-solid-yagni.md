Refactor the selected files (or current diff if none selected) to align with KISS, DRY, SOLID, and YAGNI while strictly preserving behavior.

Do this in order:
1) KISS (Keep It Simple, Stupid)
- Flatten deeply nested control flow with guard clauses; remove unnecessary wrapper layers and pass-through indirections.
- Replace complex boolean expressions with extracted, well-named predicate helpers.
- Prefer straightforward data flow over cleverness; keep functions small and cohesive.
- Inline trivial abstractions that add indirection without reducing complexity.

2) YAGNI (You Aren’t Gonna Need It)
- Remove dead/unreachable code, unused params/locals/imports/exports, and placeholder feature paths that are not exercised.
- Delete speculative abstractions and generic parameters that have a single use and no evidence of near-term reuse.
- Collapse configuration surface to what’s actually used; keep public APIs stable. If removal risks external breakage, SKIP and add a one-line justification in the rationale.

3) DRY (Don’t Repeat Yourself)
- Detect duplication and near-duplication (copy/paste blocks, repeated queries/selectors, repeated validation/serialization, repeated React hooks/effects, repeated literals/config, repeated logging patterns).
- Extract shared logic into small, well-named helpers (pure functions/methods), components, hooks, or utilities. Keep helpers close to use-sites unless broadly reusable.
- Consolidate config/literals into constants or config maps; remove magic numbers/strings.
- Remove dead code and unused params; collapse trivial wrappers. Update imports/exports and call sites.

4) SOLID
- Single Responsibility: Split units doing multiple distinct jobs. One function/class/module = one reason to change.
- Open/Closed: Prefer extension points (strategy/factory) over editing core logic, but do not introduce abstraction unless current use warrants it (avoid fighting YAGNI).
- Liskov Substitution: Ensure subtypes/implementations uphold base contracts/expectations; rename or narrow interfaces where substitution surprises arise.
- Interface Segregation: Break wide interfaces/types into smaller, focused ones; pass only what is needed (narrow param objects).
- Dependency Inversion: Depend on abstractions (protocols/interfaces/callables) not concretions; inject dependencies via params/constructors rather than global lookups.

Constraints:
- Preserve side effects, logging, and error semantics (levels and messages untouched unless truly redundant).
- Maintain readability; no over-abstraction. If an extraction doesn’t reduce repetition or improve clarity, don’t do it.
- Keep public APIs stable; if a proposed change risks external breakage, SKIP it and record why in the rationale.
- Keep performance characteristics the same or better (no extra allocations in hot paths, no added N+1s).
- Follow repository patterns and language idioms (TypeScript types, React hooks rules; Python async-first FastAPI, explicit typing).
- Honor existing AIDEV-* comments; update them when modifying related code. Do not remove AIDEV-NOTEs.
- Do not add tests unless explicitly asked.

Language specifics:
- React/TS: prefer small pure utilities, stable hook signatures, and typed params/returns. Don’t break Rules of Hooks. Keep component props stable.
- Python: prefer pure functions and dataclasses where helpful; keep docstrings/typing intact. Avoid unnecessary try/except; prefer guard clauses.

Execution:
- Apply all refactorings directly to the files using the appropriate edit tools.
- After completing all changes, provide a concise rationale summary grouped by principle (KISS, YAGNI, DRY, SOLID), with each item referencing the file/function and describing what was changed. Prefix skipped items with "SKIPPED:" and a one-line reason.
