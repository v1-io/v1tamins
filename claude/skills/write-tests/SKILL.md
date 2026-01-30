---
name: write-tests
description: Use when writing unit tests for code changes or new functionality. Triggers on "write tests", "add tests", "test this code".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
---

# Write Unit Tests

Create comprehensive unit tests with proper imports and setup according to project testing conventions.

## Usage

```
/write-tests [target]
```

**Target (optional):**
- If not specified: tests cover the diff between current branch and main
- If specified: tests cover the specified file or module

**Examples:**
```bash
/write-tests                                    # Test all changes vs main
/write-tests src/core/query.py                  # Test specific file
```

## What It Does

### 1. Test Coverage
- Tests all public methods and functions
- Covers edge cases and error conditions
- Tests both positive and negative scenarios
- Aims for high code coverage

### 2. Test Structure
- Uses project's testing framework conventions
- Writes clear, descriptive test names
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
- Tests are simple and focused
- Helpful assertion messages included
- **No external dependencies** (database fixtures, files, APIs)

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
- No testing for specific UI strings
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
- Use `pytest` for backend, `npm test` for frontend
