---
name: fix-tests
description: Systematically fix all failing tests until everything passes
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# Fix Failing Tests

Use this when you have failing test output. The goal is to **fix ALL failing tests, re-run tests, and iterate until everything passes**.

## Usage

```
/fix-tests
```

Use this after you've pasted test failure output into the conversation.

## What It Does

1. **Understands ALL Failures**
   - Reads entire test log (pytest / Jest / parallel tests)
   - Checks "Test Results" summary for ALL failing services (looks for `✗` markers)
   - Checks "Failed Test Details" for MULTIPLE failing services
   - Notes ALL services that failed (common, analyst, config, rag_queen, frontend-lint, frontend-tests)
   - Creates list of all failures before starting fixes

2. **Fixes EACH Failure**
   - For EACH failing service/group:
     - Opens failing test files and implementation files
     - Makes smallest, clearest change
     - Prefers fixing implementation over changing tests
   - Fixes ALL failures before proceeding

3. **Re-runs Tests for EACH Fix**
   - Backend: `commander test <service>` (or with `-k` for specific tests)
   - Frontend: `cd web && npm run lint` or `npm run test`
   - Verifies each group passes before moving to next
   - Repeats if tests still fail

4. **Re-runs Full Test Suite**
   - **CRITICAL**: Always re-runs original command (e.g., `scripts/run_parallel_tests.sh`)
   - Catches hidden failures or new failures from fixes
   - Only stops when full suite passes with zero failures

## Important Notes

- Don't stop after fixing one failure - check for multiple failing groups
- Always re-run full parallel suite after fixes
- Parse entire error output - summary AND detailed sections

## Testing Commands

**Backend (in .venv):**
```bash
commander test <service>              # All unit tests
commander test <service> -k "pattern" # Specific tests
commander test <service> --integration # Integration tests
```

**Frontend:**
```bash
cd web && npm run lint
cd web && npm run test -- --all --ci=false --watchAll=false
```

**Full Suite:**
```bash
scripts/run_parallel_tests.sh
```
