---
name: refactor
description: Refactor code applying KISS, DRY, SOLID, and YAGNI principles
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# KISS DRY SOLID YAGNI Refactor

Refactor selected files (or current diff) to align with KISS, DRY, SOLID, and YAGNI while strictly preserving behavior.

## Usage

```
/refactor [file_or_pattern]
```

**Examples:**
```bash
/refactor                              # Refactor current diff
/refactor src/core/*.py                # Refactor specific files
```

## Principles Applied (In Order)

### 1. KISS (Keep It Simple, Stupid)
- Flatten deeply nested control flow with guard clauses
- Remove unnecessary wrapper layers and pass-through indirections
- Replace complex boolean expressions with well-named predicates
- Prefer straightforward data flow over cleverness
- Keep functions small and cohesive
- Inline trivial abstractions that add indirection without reducing complexity

### 2. YAGNI (You Aren't Gonna Need It)
- Remove dead/unreachable code, unused params/locals/imports/exports
- Delete speculative abstractions with single use and no near-term reuse
- Collapse configuration surface to what's actually used
- Keep public APIs stable (SKIP if removal risks breakage)

### 3. DRY (Don't Repeat Yourself)
- Detect duplication: copy/paste blocks, repeated queries/hooks/effects
- Extract shared logic into small, well-named helpers
- Consolidate config/literals into constants
- Remove magic numbers/strings
- Keep helpers close to use-sites unless broadly reusable

### 4. SOLID
- **Single Responsibility**: One function/class = one reason to change
- **Open/Closed**: Prefer extension points over editing core logic (when warranted)
- **Liskov Substitution**: Subtypes uphold base contracts
- **Interface Segregation**: Break wide interfaces into focused ones
- **Dependency Inversion**: Depend on abstractions, inject dependencies

## Constraints

- **Preserve behavior**: No functional changes
- **Preserve side effects**: Logging and error semantics untouched
- **Maintain readability**: No over-abstraction
- **Keep public APIs stable**: Skip changes that risk breakage
- **Same or better performance**: No extra allocations in hot paths
- **Follow repo patterns**: TypeScript types, React hooks rules, Python async-first
- **Honor AIDEV-* comments**: Update when modifying related code
- **No tests unless asked**

## Language Specifics

**React/TypeScript:**
- Prefer small pure utilities, stable hook signatures, typed params/returns
- Don't break Rules of Hooks
- Keep component props stable

**Python:**
- Prefer pure functions and dataclasses
- Keep docstrings/typing intact
- Avoid unnecessary try/except, prefer guard clauses

## Output

Concise rationale summary grouped by principle:

```
## KISS
- Flattened nested if/else in `query.py:process_result` using guard clauses

## YAGNI
- Removed unused `legacy_mode` parameter in `handler.py:handle_request`
- SKIPPED: `config.defaults` removal - used by external clients

## DRY
- Extracted `validate_user_input()` helper in `api.py` (was duplicated 3x)

## SOLID
- Split `UserManager` into `UserReader` and `UserWriter` (SRP)
```
