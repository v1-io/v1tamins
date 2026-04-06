---
name: write-tests
description: "Use when writing unit tests, adding test coverage for code changes, or generating tests for a specific file or module. Triggers on 'write tests', 'add tests', 'test this code', 'add test coverage', 'generate unit tests'."
allowed-tools: "Bash, Read, Write, Edit, Grep"
---

# Write Unit Tests

Creates comprehensive unit tests following project conventions. Covers public methods, edge cases, and error paths using Arrange-Act-Assert.

## Usage

```
/write-tests [target]
```

- **No target**: tests cover the diff between current branch and main
- **With target**: tests cover the specified file or module (e.g. `src/core/query.py`)

## Workflow

### 1. Analyze Target Code

Reads the target file(s) and identifies public methods, branches, and error conditions to test. Detects the project's testing framework (pytest, Jest, Vitest) and follows its conventions.

### 2. Generate Tests

Creates tests covering:
- Happy path scenarios
- Edge cases and boundary conditions
- Error handling and exception cases
- External dependency mocking (only where necessary)

### 3. Verify Tests Pass

Runs the test suite to confirm all new tests pass:
- Backend: `pytest`
- Frontend: `npm test`

## Project Conventions

**Backend (pytest):** Place in `tests/unit/` or `tests/integration/`. Use fixtures from `conftest.py`. Prefer real objects over mocks except for LLM calls.

**Frontend (Jest/Vitest):** Place in `__tests__/` mirroring `src/`. Share mock utilities in `testUtils.ts`. Mock all external API calls.

**Style:** Arrange-Act-Assert pattern. Descriptive names (`test_method_condition_expected_result`). Isolated and deterministic.

## Anti-Patterns to Avoid

Three iron laws:
1. **Never test mock behavior** — assert on real component output, not mock test IDs
2. **Never add test-only methods to production classes** — put cleanup in `test-utils/`
3. **Never mock without understanding dependencies** — run with real implementation first

**Red flags:** Mock setup >50% of test, assertions on `*-mock` IDs, methods only called in test files.

**Gate before each mock:**

| Question | If No... |
|----------|----------|
| What side effects does the real method have? | Don't mock yet |
| Does this test depend on those side effects? | Mock at lower level |
| Do I fully understand what this test needs? | Run with real impl first |
