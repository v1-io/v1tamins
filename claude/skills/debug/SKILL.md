---
name: debug
description: "Analyzes stack traces, traces error propagation through call chains, identifies root causes in code, and suggests targeted fixes with regression tests. Use when debugging errors, diagnosing failures, or investigating why tests or services are failing. Triggers on 'debug this', 'why is this failing', 'trace the error', 'fix this error', 'investigate failure'."
allowed-tools: "Bash, Read, Edit, Grep"
---

# Debug Error

Systematically traces errors to their root cause and applies a durable fix. Invoke after pasting an error message, log output, or describing a failure.

## Usage

```
/debug
```

## Workflow

### 1. Understand the Failure

Extract structured information from the error:

```bash
# Gather context
git log --oneline -5                    # Recent changes that may have introduced the bug
git diff HEAD~3 --name-only             # Files changed recently
```

Identify: error type and message, stack trace (file, line, function), triggering inputs, execution environment (service, working directory, env vars).

### 2. Trace Root Cause

Walk the call stack upward until finding the first invalid state or data:

1. Read the failing function and inspect its inputs (params, config, environment, `cwd`)
2. Check each caller in the stack for where data goes wrong
3. For test failures, narrow scope: `pytest --collect-only -q` then `pytest -k "test_name" -x`
4. Check recent changes for regressions: `git log --oneline -10 -- <failing-file>`
5. Classify: data issue, state issue, logic error, integration mismatch, or configuration problem

If the cause is unclear, add temporary instrumentation:

```python
import sys, traceback

def debug_context(note, **kwargs):
    print(f"DEBUG {note}: {kwargs}", file=sys.stderr)
    print(''.join(traceback.format_stack(limit=15)), file=sys.stderr)
```

### 3. Validate Root Cause

Confirm the hypothesis explains the observed failure:

1. Write a minimal reproduction or targeted test that triggers the bug
2. Verify the root cause is the **source**, not a downstream symptom
3. Scan for other code paths that could hit the same issue

**If validation fails:** return to step 2 and broaden the search — check adjacent layers, environment differences, or timing-dependent state.

### 4. Apply Fix and Verify

1. Fix the underlying bug, not the symptom
2. If multiple fixes are possible, list trade-offs and pick the safest
3. Add defense-in-depth at boundaries (input validation, fail-fast)
4. Remove any temporary instrumentation
5. Run the reproduction test to confirm the fix resolves the issue
6. Add a regression test if one doesn't exist
7. Follow project standards: logging levels (`warning` for expected, `error` with `exc_info=True` for unexpected), async-first for FastAPI, scoped changes

**If the fix doesn't resolve the error:** re-run the reproduction, check for secondary causes, and return to step 2.
