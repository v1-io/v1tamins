---
name: v1-deslop
description: Use when removing AI-generated slop, cleaning up verbose code, or removing unnecessary defensive checks. Triggers on "remove slop", "clean up AI code", "deslop".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Remove AI Code Slop

Check the diff against main and remove branch-introduced code that adds no behavior, proof, or maintainability value.

Use `v1-simplify` for broader reuse/quality/efficiency cleanup. Use this skill when the target is recognizable agent-generated residue: defensive wrappers, narration comments, casts, logging, or abstraction created without a concrete need.

## Usage

Typical invocations:
- Claude Code: `/v1-deslop`
- Codex: invoke `v1-deslop` from the skills menu or use `$v1-deslop`

## Removal Gate

Remove a line, block, helper, or wrapper only when at least one condition is true:

- It duplicates existing project behavior or adjacent patterns.
- It handles a state already ruled out by validation, typing, or caller contract.
- It narrates obvious code instead of documenting a hidden constraint.
- It hides a type/design problem with `any`, broad casting, or catch-all fallback.
- It adds logging, retries, configuration, or abstraction without a caller, failure mode, or test.

Keep it when it protects a real trust boundary, documents a non-obvious invariant, preserves public API compatibility, or is needed by existing behavior.

## What It Removes

- **Extra comments** that a human wouldn't add or are inconsistent with the rest of the file
- **Extra defensive checks** or try/catch blocks that are abnormal for that area of the codebase (especially if called by trusted/validated codepaths)
- **Casts to `any`** to get around type issues
- **Over-engineered patterns** that don't match the file's existing style
- **Unnecessary type annotations** on obvious types
- **Verbose error handling** where simpler patterns exist
- **Redundant null checks** in already-validated paths
- **Excessive logging** beyond what's normal for the codebase

## What It Preserves

- Actual bug fixes and intended functionality
- Comments that provide genuine value
- Defensive code at trust boundaries (user input, external APIs)
- Type annotations that improve clarity

## Process

1. Get the diff between current branch and main.
2. Review each changed file for the Removal Gate conditions.
3. Remove only gated slop while preserving intended behavior.
4. Run the smallest relevant formatter, typecheck, lint, or test command available.
5. Report a 1-3 sentence summary of what changed and which check ran.

## Output

A brief summary like:
> "Removed 3 unnecessary try/catch blocks in `query.py`, deleted 5 redundant comments in `handler.ts`, and removed 2 `any` casts that were hiding type issues."
