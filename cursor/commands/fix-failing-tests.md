# Fix Failing Tests

## Overview

Use this when you already have failing test output in the conversation (for example from the `parallel-tests` pre-commit hook). The goal is to **fix ALL failing tests or code, re-run the same tests, and keep iterating until everything passes**.

## Steps

1. **Understand what failed - CHECK ALL FAILURES**
   - Read the ENTIRE test log (pytest / Jest / `scripts/run_parallel_tests.sh`).
   - **CRITICAL**: Check the "Test Results" summary section for ALL failing services/groups (look for `✗` markers).
   - **CRITICAL**: Check the "Failed Test Details" section - there may be MULTIPLE failing services, not just one.
   - Note ALL services/commands that failed (e.g. `common`, `analyst`, `config`, `rag_queen`, `frontend-lint`, `frontend-tests`) and the exact test names and error messages for EACH.
   - Create a list of all failing groups before starting fixes.

2. **Locate and fix EACH failure**
   - For EACH failing service/group identified in step 1:
     - Open the failing test file(s) and the corresponding implementation file(s) referenced in the stack trace or import paths.
     - Make the smallest, clearest change that makes the test's expectations correct and consistent with existing patterns.
     - Prefer fixing implementation over changing tests unless the test is clearly out of date.
   - Fix ALL failures before moving to step 3.

3. **Re-run the relevant tests for EACH fix (inside `.venv` for Python)**
   - For EACH service/group you fixed:
     - Backend groups: `python -m tools.commander.commander.cli test <service>` (optionally with `-k` to narrow to the failing test[s]).
     - Frontend: `cd web && npm run lint` or `cd web && npm run test -- --all --ci=false --watchAll=false`, matching the original failure.
     - Verify this specific group passes before moving to the next one.
   - If any tests are still failing, repeat Step 2–3 for that group until it's green.

4. **ALWAYS re-run the full parallel test suite**
   - **CRITICAL**: After fixing individual groups, ALWAYS re-run the same top-level command that originally failed (e.g. `scripts/run_parallel_tests.sh` or the `parallel-tests` pre-commit hook).
   - This catches any failures that were hidden or any new failures introduced by your fixes.
   - If the full suite reveals NEW failures, go back to step 1 and add them to your list.
   - Stop ONLY when the full parallel test suite passes with zero failures.

## Important Notes

- **Don't stop after fixing one failure** - always check if there are multiple failing groups in the original output.
- **Always re-run the full parallel suite** after fixes - don't assume fixing one thing means everything passes.
- **Parse the entire error output** - look at both the summary section AND the detailed failure sections.

## Checklist

- [ ] ALL failing services/groups identified from the summary section
- [ ] ALL failing test names and error messages understood for each group
- [ ] ALL failures fixed (implementation or test updates)
- [ ] Each fixed group verified individually to pass
- [ ] Full parallel test suite re-run and passes with zero failures
