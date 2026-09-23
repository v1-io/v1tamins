---
name: v1-fix-tests
description: Use when a failing test suite needs systematic repair. Triggers on "fix tests", "tests failing", or "make tests pass".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Fix Failing Tests

Use this when you have failing test output. Done means the original test command exits with zero failures; re-run it after your last fix.

## Usage

Typical invocations:
- Claude Code: `/v1-fix-tests`
- Codex: invoke `v1-fix-tests` from the skills menu or use `$v1-fix-tests`

Use this after you've pasted test failure output into the conversation.

## What It Does

1. **Understands the Failures**
   - Reads the entire test log (pytest / Jest / parallel tests), both the summary and the detailed sections
   - Lists every failing test and test group (backend, frontend, linting, etc.) before starting fixes
   - Confirms the failing command is a reliable feedback loop for the user-visible problem; if not, first narrow or rebuild the loop using the `v1-debug` skill

2. **Fixes Each Failure**
   - Opens failing test files and implementation files
   - Makes the smallest, clearest change
   - Prefers fixing implementation over changing tests

3. **Re-runs Tests**
   - Re-runs the affected tests after each fix, narrowed with the runner's filter (for example `pytest -k`)

## Important Notes

- Prefer fixing code over weakening assertions; only change tests when the test is wrong or the intended behavior changed. When a test itself must change, follow the mock-discipline and assertion rules in `v1-write-tests` rather than restating them here.
- If the failure is flaky rather than a real regression, hand off to `v1-debug` to stabilize the reproduction (measure the failure rate; isolate time, randomness, filesystem, and network) before patching.

