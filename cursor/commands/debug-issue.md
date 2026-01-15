# Debug Error

## Overview
Guided steps for diagnosing a pasted error/log message or description of a failure and producing a durable fix.

## Review Steps

### Understand the Failure
- [ ] Extract error type, message, codes, stack trace, and reproduction steps
- [ ] Capture expected vs actual behavior and confirm current environment/context
- [ ] Pinpoint failing module/function and triggering inputs
- [ ] Note execution context: service/container, current working directory, relevant env vars; confirm `.venv` active and Tilt status

### Trace Root Cause
- [ ] Ask “what called this?”; walk upward until the first invalid state/data
- [ ] Inspect inputs at each layer (params, config, environment, `cwd`)
- [ ] If unclear, add short-lived instrumentation to print context + stack to stderr near the risky operation; remove after
- [ ] If failure appears only in tests, narrow with `commander test <service> --collect-only`, `-p`, `-k`, `--watch`
- [ ] Classify the issue (data, state, logic, integration, configuration)
- [ ] Check surrounding code and recent changes for regressions
- [ ] Record the original trigger and fix at the source (not only the symptom)

Temporary instrumentation (Python):
```python
import sys, traceback

def debug_context(note, **kwargs):
    print(f"DEBUG {note}: {kwargs}", file=sys.stderr)
    print(''.join(traceback.format_stack(limit=15)), file=sys.stderr)
```

### Validate Root Cause
- [ ] Explain how the root cause produces the observed failure
- [ ] Scan for other paths that could hit the same issue
- [ ] Prove via minimal reproduction or targeted test that the behavior flips from FAIL → PASS with the fix

### Plan the Fix
- [ ] Address the underlying bug, not only the symptom
- [ ] Outline candidate fixes, note trade-offs, and specify chosen approach
- [ ] Provide a step-by-step resolution plan, including guards/validation or logging updates
- [ ] Suggest targeted tests or monitoring to prevent recurrence
- [ ] Add defense-in-depth: validate inputs at boundaries, fail fast early, add targeted tests

### Project Standards
- [ ] Respect/update existing `AIDEV-*` notes; add compliance notes when needed
- [ ] Follow logging levels (warning for expected, error with `exc_info=True` for unexpected)
- [ ] Keep FastAPI code async-first and changes scoped to the fix
