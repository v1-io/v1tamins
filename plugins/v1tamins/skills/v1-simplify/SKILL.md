---
name: v1-simplify
description: Use when reviewing recent code changes for reuse, unnecessary complexity, quality issues, or efficiency problems before considering the work done. Triggers on "simplify", "clean up this diff", "review for reuse", "make this simpler", "quality pass", "efficiency pass".
---
# Simplify

Review the changed code for reuse, quality, and efficiency issues, then fix the problems that are worth addressing.

Use this for a bounded cleanup of the current diff. Use `v1-refactor` when the user asks to refactor selected files while preserving behavior. Use `v1-deep-review` when the right output is structural review feedback rather than edits.

## Quick Start

1. Inspect the current diff with `git diff`; use `git diff HEAD` when staged changes are present.
2. If there is no diff, inspect the files most recently edited or explicitly mentioned by the user.
3. Run three review passes: reuse, quality, and efficiency.
4. Apply fixes directly for valid findings.
5. Summarize what changed, or say the code was already clean.

## Review Passes

Run the three passes independently. When the host supports subagents or parallel review workers, launch all three with the same diff context before applying fixes. When it does not, run the passes sequentially in the main thread.

Honor any user-supplied focus, such as memory efficiency, API clarity, or reducing duplicate code, while still checking the full changed surface.

### Code Reuse

Search for existing project code that can replace new or expanded logic.

Check for:
- New functions that duplicate helpers, utilities, shared modules, or adjacent file patterns
- Inline logic that should use an existing helper
- Hand-rolled string manipulation, path handling, environment checks, type guards, parsing, or formatting
- Similar code blocks that already exist elsewhere in the repository

Prefer established local helpers over new abstractions. Only add an abstraction when it removes real duplication or clearly matches project patterns.

### Code Quality

Look for complexity, weak boundaries, and future-change costs introduced by the current diff.

Check for:
- Redundant state that can be derived from existing data
- Cached values, observers, or effects where direct computation or direct calls would be clearer
- Parameter sprawl added to avoid restructuring a function or object
- Copy-paste with slight variation that should be unified
- Leaky abstractions that expose internal details or break module boundaries
- Stringly typed values where constants, enums, unions, or branded types already exist
- Unnecessary wrappers, especially JSX or layout elements that add no behavior or layout value
- Comments that narrate what the code does, reference the task, or explain obvious identifiers

Keep comments that explain non-obvious why: hidden constraints, subtle invariants, compatibility requirements, and intentional workarounds.

### Efficiency

Look for unnecessary work and avoidable runtime cost.

Check for:
- Redundant computation, repeated file reads, duplicate network calls, or repeated API calls
- N+1 access patterns introduced by loops or nested lookups
- Independent operations that now run sequentially without a reason
- Blocking work added to startup, render, request, or other hot paths
- Unconditional state/store updates inside polling loops, intervals, or event handlers
- Wrapper updater functions that ignore same-reference returns or other no-change signals
- Existence pre-checks that introduce time-of-check/time-of-use races instead of handling the operation error
- Unbounded data structures, missing cleanup, or event listener leaks
- Broad reads or loads where targeted access would be enough

Add change-detection guards when recurring updates can fire without changing observable state.

## Fixing

Aggregate findings from all passes before editing. Fix each valid issue directly and keep the scope tied to the current diff.

Fix only when the cleanup has a concrete reason: removes duplication, deletes unnecessary state/work, restores an existing pattern, narrows a boundary, or reduces a measurable runtime/re-render/retry cost.

Skip false positives and low-value changes without debate. Do not refactor unrelated code just because it is nearby.

After edits, run the smallest relevant verification command available in the project. If no command is obvious, inspect the resulting diff carefully and report that no automated verification was run.

## Output

Finish with a concise summary:
- What simplifications or cleanups were made
- Which verification command ran, if any
- Any notable findings intentionally skipped
