---
name: v1-write-tests
description: Use when writing unit tests for code changes or new functionality. Triggers on "write tests", "add tests", "test this code".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
---
# Write Unit Tests

Add focused tests for changed behavior, bug seams, boundary cases, and regression risk using the project's existing test conventions.

## Usage

Typical invocations:
- Claude Code: `/v1-write-tests [target]`
- Codex: invoke `v1-write-tests` from the skills menu or use `$v1-write-tests [target]`

**Target (optional):**
- If not specified: tests cover the diff between current branch and main
- If specified: tests cover the specified file or module

Examples:
```bash
/v1-write-tests                                    # Test all changes vs main
/v1-write-tests src/core/query.py                  # Test specific file
```

In Codex, the slash examples below map directly to `$v1-write-tests ...`.

## What It Does

### 1. Test Selection
- Identify the changed public behavior from the diff, target file, or user request.
- For bug fixes, reproduce the real failure pattern at the narrowest correct seam before asserting the fix.
- Cover boundary and error paths that the changed behavior can realistically hit.
- Add a test only when it can fail for a meaningful regression; skip coverage that only executes lines.
- For each changed branch or state transition, prefer at least one assertion that would fail if that branch were removed, inverted, or bypassed.

### 2. Test Structure
- Uses project's testing framework conventions
- Names each test after the behavior and condition under test
- Follows Arrange-Act-Assert pattern
- Groups related tests logically

### 3. Test Cases Include
- Happy path scenarios
- Edge cases and boundary conditions
- Error handling and exception cases
- Appropriate mocking of external dependencies

### 4. Test Quality
- Tests are independent and isolated
- Tests are deterministic and repeatable
- Each test has one primary reason to fail
- Assertion messages or comments explain non-obvious invariants only
- External APIs, wall-clock time, network calls, and shared mutable state are isolated behind fixtures, fakes, or test doubles unless the project explicitly uses integration tests for that layer

## Project-Specific Conventions

**Backend (pytest):**
- Location: `tests/unit/` or `tests/integration/` (follow project conventions)
- Fixtures in `conftest.py`
- Use real objects (not mocks) except for LLM calls
- Auto-marked by directory (unit vs integration)

**Frontend (Jest/Vitest):**
- Location: `__tests__/` mirroring `src/` structure
- Mocks in `__mocks__/`
- Share mocking functions in `testUtils.ts`
- Mock all external API calls

**Style:**
- Arrange-Act-Assert pattern
- Descriptive test names (test_method_condition_expected_result)
- Test user-visible UI text when it is the behavior; otherwise prefer roles, labels, states, and user outcomes over brittle copy assertions
- Isolated and deterministic

## What NOT to Do (Anti-Patterns)

### The Iron Laws

```
1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies
```

### Anti-Pattern 1: Testing Mock Behavior

**Bad:**
```typescript
// Testing that mock exists, not real behavior
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**Fix:** Test real component or don't mock it. If you must mock, don't assert on mock elements.

### Anti-Pattern 2: Test-Only Methods in Production

**Bad:** Adding `destroy()` to a class only because tests need cleanup.

```typescript
// BAD: destroy() only used in tests
class Session {
  async destroy() { /* cleanup */ }
}

// In tests
afterEach(() => session.destroy());
```

**Fix:** Put cleanup utilities in test-utils/, not production code.

```typescript
// GOOD: Test utility
// test-utils/cleanup.ts
export async function cleanupSession(session: Session) {
  const workspace = session.getWorkspaceInfo();
  if (workspace) await workspaceManager.destroyWorkspace(workspace.id);
}

// In tests
afterEach(() => cleanupSession(session));
```

### Anti-Pattern 3: Mocking Without Understanding

**Bad:** Mocking "to be safe" without understanding what the test depends on.

```typescript
// Mock breaks test logic - method had side effects test needed!
vi.mock('ToolCatalog', () => ({
  discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
}));

await addServer(config);
await addServer(config);  // Should throw - but won't!
```

**Fix:** Run test with real implementation first, then add minimal mocking.

### Anti-Pattern 4: Incomplete Mocks

**Bad:** Mocking only fields you think you need.

```typescript
const mockResponse = {
  status: 'success',
  data: { userId: '123' }
  // Missing: metadata that downstream code uses
};
```

**Fix:** Mirror the complete real API response structure.

### Red Flags

- Assertion checks for `*-mock` test IDs
- Methods only called in test files
- Mock setup is >50% of test
- "Mocking just to be safe"
- Test fails when you remove mock
- Regression test cannot fail for the original bug because it bypasses the real call path

### Gate Function

Before each mock, ask: "Do I understand what this test actually needs?"

| Question | If No... |
|----------|----------|
| What side effects does the real method have? | Don't mock yet |
| Does this test depend on any of those side effects? | Mock at lower level |
| Do I fully understand what this test needs? | Run with real impl first |

## Notes

- Only write tests when explicitly requested
- Always run tests after creating them to verify they pass
- Use the project-native test command. If no command is obvious, inspect package scripts, test config, Makefile, or repo docs before guessing.
