---
name: write-tests
description: Create comprehensive unit tests for code changes
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

## Notes

- Only write tests when explicitly requested
- Always run tests after creating them to verify they pass
- Use `pytest` for backend, `npm test` for frontend
