---
name: debug
description: Systematically diagnose errors and produce durable fixes
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# Debug Error

Guided workflow for diagnosing errors/failures and producing a durable fix.

## Usage

```
/debug
```

Use this after pasting an error message, log output, or describing a failure.

## What It Does

### 1. Understand the Failure
- Extracts error type, message, codes, stack trace, reproduction steps
- Captures expected vs actual behavior and environment/context
- Pinpoints failing module/function and triggering inputs
- Notes execution context: service/container, working directory, env vars
- Confirms `.venv` active and Tilt status

### 2. Trace Root Cause
- Walks call stack upward until finding first invalid state/data
- Inspects inputs at each layer (params, config, environment, `cwd`)
- Adds temporary instrumentation if unclear (prints context to stderr)
- For test failures: narrows with `commander test <service> --collect-only`, `-k`, etc.
- Classifies issue (data, state, logic, integration, configuration)
- Checks surrounding code and recent changes for regressions
- Records original trigger and fixes at the source (not symptom)

**Temporary instrumentation (Python):**
```python
import sys, traceback

def debug_context(note, **kwargs):
    print(f"DEBUG {note}: {kwargs}", file=sys.stderr)
    print(''.join(traceback.format_stack(limit=15)), file=sys.stderr)
```

### 3. Validate Root Cause
- Explains how root cause produces observed failure
- Scans for other paths that could hit same issue
- Proves via minimal reproduction or targeted test

### 4. Plan the Fix
- Addresses underlying bug, not symptom
- Outlines candidate fixes, notes trade-offs
- Provides step-by-step resolution plan
- Suggests targeted tests or monitoring to prevent recurrence
- Adds defense-in-depth: validates inputs at boundaries, fails fast

### 5. Apply Project Standards
- Respects/updates existing `AIDEV-*` notes
- Follows logging levels (warning for expected, error with `exc_info=True` for unexpected)
- Keeps FastAPI code async-first
- Scopes changes to the fix

## Notes

- Always trace to root cause before fixing
- Add temporary instrumentation if needed, remove after
- Validate the fix resolves the issue
- Consider adding tests to prevent recurrence
