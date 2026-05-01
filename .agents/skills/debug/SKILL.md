---
name: debug
description: Use when debugging errors, diagnosing failures, performance regressions, flaky behavior, or tracing root causes from error output. Triggers on "debug this", "diagnose this", "why is this failing", "trace the error".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# Debug Error

Guided workflow for diagnosing errors/failures and producing a durable fix.

## Usage

Typical invocations:
- Claude Code: `/debug`
- Codex: invoke `debug` from the skills menu or use `$debug`

Use this after pasting an error message, log output, performance regression, flaky behavior, or describing a failure.

## What It Does

### 1. Build a Feedback Loop
- Create the fastest agent-runnable pass/fail signal that reproduces the user-described symptom
- Prefer, in order: focused failing test, CLI command with fixture input, HTTP/curl script, browser automation, captured trace replay, small harness, fuzz/property loop, or `git bisect run`
- For flaky bugs, raise the reproduction rate instead of waiting for a perfect repro: loop the trigger, increase stress, pin time, seed randomness, isolate filesystem/network, and narrow timing windows
- Make the loop sharper before fixing: assert the exact symptom, keep it deterministic, and reduce runtime where possible
- If no loop is possible, stop and say what was tried; ask for an artifact, access to the reproducing environment, or approval for temporary instrumentation

Do not proceed to root-cause hypotheses until the loop reproduces the real user-visible failure or a documented high-rate version of the flaky failure.

### 2. Reproduce and Capture
- Extracts error type, message, codes, stack trace, reproduction steps
- Captures expected vs actual behavior and environment/context
- Pinpoints failing module/function and triggering inputs
- Notes execution context: service/container, working directory, env vars
- Confirms environment is properly configured
- Confirms the loop reproduces the failure mode the user described, not just a nearby failure
- Captures exact evidence that the later fix must eliminate: error text, wrong output, status code, timing, screenshot, log line, or trace id

### 3. Rank Hypotheses
- Generate 3-5 ranked, falsifiable hypotheses before instrumenting or patching
- For each hypothesis, state the prediction: "If this is the cause, then this probe/change will make the failure disappear, move, or worsen"
- Prefer hypotheses tied to observed evidence, recent changes, boundaries between modules, data-shape assumptions, and environment differences
- Share the ranked list when user domain knowledge could cheaply re-rank it, but continue with the best current ranking if the user is unavailable

### 4. Instrument and Trace Root Cause
- Walks call stack upward until finding first invalid state/data
- Inspects inputs at each layer (params, config, environment, `cwd`)
- Adds targeted temporary instrumentation only where it distinguishes hypotheses
- For test failures: narrows with `pytest --collect-only`, `-k`, etc.
- Classifies issue (data, state, logic, integration, configuration)
- Checks surrounding code and recent changes for regressions
- Records original trigger and fixes at the source (not symptom)
- Changes one variable at a time; avoid broad "log everything and grep" probes
- For performance regressions, establish a timing/profile/query-plan baseline before changing code

**Temporary instrumentation (Python):**
```python
import sys, traceback

def debug_context(note, **kwargs):
    print(f"[DEBUG-a4f2] {note}: {kwargs}", file=sys.stderr)
    print(''.join(traceback.format_stack(limit=15)), file=sys.stderr)
```

Use a unique `[DEBUG-<id>]` prefix for every temporary probe so cleanup is a single grep.

### 5. Validate Root Cause
- Explains how root cause produces observed failure
- Scans for other paths that could hit same issue
- Proves via the feedback loop, minimal reproduction, targeted test, or measurement baseline

### 6. Plan and Apply the Fix
- Addresses underlying bug, not symptom
- Outlines candidate fixes, notes trade-offs
- Provides step-by-step resolution plan
- Suggests targeted tests or monitoring to prevent recurrence
- Adds defense-in-depth: validates inputs at boundaries, fails fast
- Keeps changes scoped to the proven root cause

### 7. Add the Right Regression Test
- Convert the minimized repro into a failing regression test before the fix when there is a correct seam
- Use a seam that exercises the real bug pattern as it occurs at the call site
- Do not add shallow tests that cannot fail for the original bug; they create false confidence
- If no correct seam exists, document that as an architectural finding and still re-run the original feedback loop after the fix

### 8. Cleanup and Handoff
- Respects/updates existing `AIDEV-*` notes
- Follows logging levels (warning for expected, error with `exc_info=True` for unexpected)
- Keeps FastAPI code async-first
- Scopes changes to the fix
- Removes all temporary `[DEBUG-...]` instrumentation and throwaway harnesses unless they are intentionally promoted into tests/tools
- States the winning hypothesis and validation command in the final report, commit, or PR description
- After fixing, note what would have prevented the bug only if the evidence points to a real follow-up

## Notes

- Build the feedback loop first; diagnosis quality depends on the signal
- Always trace to root cause before fixing
- Add temporary instrumentation if needed, then remove it
- Validate the fix with the original feedback loop and any regression test
- Consider adding tests to prevent recurrence, but only at a seam that can reproduce the actual bug pattern

## Human-In-The-Loop Reproduction

When a bug requires manual clicking or access that automation cannot reach, use `scripts/hitl-loop.template.sh` as a structured last resort:

1. Copy the template to a throwaway path outside committed code, such as `/tmp/hitl-loop.sh`.
2. Edit the `step` and `capture` prompts to match the reproduction.
3. Run `bash /tmp/hitl-loop.sh`.
4. Parse the captured key/value output and feed it back into the diagnosis loop.
