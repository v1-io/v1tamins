---
name: v1-simplify
description: Use when reviewing or restructuring code on the current diff or named files for reuse, simplicity, duplication, complexity, or efficiency. Triggers on "simplify", "refactor", "clean up code", "apply DRY", "reduce complexity", "too nested".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Simplify

Review changed code (or named files) for reuse, quality, structure, cognitive complexity, and efficiency, then fix what is worth fixing while preserving behavior.

Scope defaults to the current diff; pass files or a `file:function` target to scope to specific code. Use `v1-deep-review` when the right output is structural review feedback rather than edits.

## Usage

Typical invocations:
- Claude Code: `/v1-simplify [target]`
- Codex: invoke `v1-simplify` from the skills menu or use `$v1-simplify [target]`

**Target (optional):**
- none → the current diff (`git diff`, or `git diff HEAD` when staged changes are present)
- a file or glob → those files
- `file:function` → a single function (useful for cognitive-complexity work)

If there is no diff and no target, inspect the files most recently edited or explicitly mentioned.

## Review Passes

Run the passes on the target. When the host supports subagents or parallel review workers, launch them with the same context before applying fixes; otherwise run sequentially. Honor any user-supplied focus (memory efficiency, API clarity, duplication) while still checking the full changed surface.

### 1. Reuse

Search for existing project code that can replace new or expanded logic.

- New functions that duplicate helpers, utilities, shared modules, or adjacent file patterns
- Inline logic that should use an existing helper
- Hand-rolled string manipulation, path handling, environment checks, type guards, parsing, or formatting
- Similar code blocks that already exist elsewhere in the repository

Prefer established local helpers over new abstractions. Only add an abstraction when it removes real duplication or clearly matches project patterns.

### 2. Quality and Simplicity

Reduce complexity, weak boundaries, and future-change cost. This pass folds in KISS, DRY, and cognitive-complexity work.

**KISS:**
- Flatten deeply nested control flow with guard clauses and early returns
- Remove unnecessary wrapper layers and pass-through indirection
- Replace complex boolean expressions with well-named predicates
- Split a function when one block owns multiple independent decisions, side effects, or output shapes
- Inline trivial abstractions that add indirection without reducing complexity

**DRY:**
- Extract copy/paste blocks and repeated queries/hooks/effects into small, well-named helpers
- Consolidate literals into constants; remove magic numbers and strings
- Keep helpers close to their use-sites unless broadly reusable

**Quality:**
- Redundant state that can be derived from existing data
- Cached values, observers, or effects where direct computation or direct calls would be clearer
- Parameter sprawl added to avoid restructuring a function or object
- Leaky abstractions that expose internal details or break module boundaries
- Stringly typed values where constants, enums, unions, or branded types already exist
- Unnecessary wrappers, especially JSX or layout elements that add no behavior or layout value
- Comments that narrate what the code does or restate obvious identifiers — keep comments that explain non-obvious *why* (hidden constraints, invariants, compatibility, intentional workarounds)

**Cognitive complexity** (use when a function is hard to follow, or on a `file:function` target):
- Increments (+1 each): `if`/`else if`/`else`, ternary, `for`/`while`/`do`, `catch`, `switch`/`case`, labeled `break`/`continue`, `&&`/`||` in conditions, recursion
- Nesting multiplier: each nesting level adds +1 to structures nested inside it
- Free (no increment): function/method calls, simple returns
- Target: keep each function under ~15
- Reduce it by returning early to flatten nesting, extracting complex conditions into named predicates, and breaking large functions into single-responsibility helpers

### 3. Structure (SOLID and YAGNI)

Apply when restructuring across files, not just tidying a diff.

- **SRP:** one function/class = one reason to change
- **OCP:** prefer extension points over editing core logic, when warranted
- **LSP:** subtypes uphold base contracts
- **ISP:** break wide interfaces into focused ones
- **DIP:** depend on abstractions; inject dependencies
- **YAGNI:** remove dead/unreachable code, unused params/locals/imports/exports; delete single-use speculative abstractions; collapse configuration surface to what is actually used

### 4. Efficiency

Look for unnecessary work and avoidable runtime cost.

- Redundant computation, repeated file reads, duplicate network or API calls
- N+1 access patterns introduced by loops or nested lookups
- Independent operations that now run sequentially without a reason
- Blocking work added to startup, render, request, or other hot paths
- Unconditional state/store updates inside polling loops, intervals, or event handlers
- Wrapper updater functions that ignore same-reference returns or other no-change signals
- Existence pre-checks that introduce time-of-check/time-of-use races instead of handling the operation error
- Unbounded data structures, missing cleanup, or event listener leaks
- Broad reads or loads where targeted access would be enough

Add change-detection guards when recurring updates can fire without changing observable state.

## Behavior Preservation

The gate depends on the kind of fix:

- **Pure restructures** (KISS/DRY/SOLID, complexity reduction, dead-code removal): preserve behavior. Prove equivalence with existing tests or a focused before/after command for the touched behavior. If equivalence cannot be proven from tests, snapshots, fixtures, examples, or a focused manual command, **stop and report instead of editing**.
- **Behavior-changing fixes** (efficiency changes, reuse that swaps an implementation): allowed, but call out the behavior change explicitly in the summary.

Always preserve side effects (logging, error semantics), keep public APIs stable, honor `AIDEV-*` and other anchor comments, and follow existing repo patterns — inspect nearby code before introducing a helper, type, module, or pattern.

## Language Specifics

**React/TypeScript:** prefer small pure utilities, stable hook signatures, typed params/returns; don't break the Rules of Hooks; keep component props stable.

**Python:** prefer pure functions and dataclasses; keep docstrings and typing intact; prefer guard clauses over unnecessary `try`/`except`.

## Fixing

Aggregate findings from all passes before editing. Fix each valid issue directly and keep the scope tied to the target.

Fix only when the change has a concrete reason: removes duplication, deletes unnecessary state/work, restores an existing pattern, narrows a boundary, reduces a measurable runtime/re-render/retry cost, or drops a function below the complexity target. Skip false positives and low-value changes without debate. Do not refactor unrelated code just because it is nearby. No new tests unless asked.

After edits, run the smallest relevant verification command available in the project. If no command is obvious, inspect the resulting diff carefully and report that no automated verification was run.

## Output

Finish with a concise summary:
- What was simplified or restructured, grouped by principle when it helps (reuse / KISS / DRY / SOLID / complexity / efficiency)
- Any behavior changes that were made intentionally
- Which verification command ran, if any
- Any notable findings intentionally skipped
