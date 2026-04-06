---
name: deslop
description: "Use when removing AI-generated slop from code, cleaning up verbose defensive checks, or stripping unnecessary comments and type casts added by AI. Triggers on 'remove slop', 'clean up AI code', 'deslop', 'remove AI junk', 'strip unnecessary comments'."
allowed-tools: "Bash, Read, Edit, Grep"
---

# Remove AI Code Slop

Reviews the diff against main and removes AI-generated slop while preserving intended functionality.

## Usage

```
/deslop
```

## Workflow

### 1. Get Branch Diff

```bash
git diff main HEAD --name-only
git diff main HEAD
```

### 2. Identify Slop Patterns

Scans each changed file for common AI-generated artifacts:

| Pattern | Example |
|---------|---------|
| Unnecessary comments | `// Set the variable to 5` above `x = 5` |
| Redundant try/catch | Wrapping already-safe internal calls |
| `any` casts | Casting to `any` to suppress type errors |
| Over-engineered patterns | Factory for a single use case |
| Obvious type annotations | `const x: number = 5` |
| Redundant null checks | Re-checking values already validated upstream |
| Excessive logging | Logging every step in a simple function |

### 3. Remove Slop, Preserve Intent

Removes identified slop while keeping:
- Actual bug fixes and intended functionality
- Comments that provide genuine value
- Defensive code at trust boundaries (user input, external APIs)
- Type annotations that improve clarity

### 4. Report Changes

Outputs a 1-3 sentence summary, e.g.:
> "Removed 3 unnecessary try/catch blocks in `query.py`, deleted 5 redundant comments in `handler.ts`, and removed 2 `any` casts that were hiding type issues."
