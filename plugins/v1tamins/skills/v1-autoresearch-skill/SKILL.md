---
name: v1-autoresearch-skill
description: >-
  Autonomous optimization loop inspired by Karpathy's AutoResearch, run when the user
  explicitly asks for it. Point the skill at any measurable target and it will modify,
  measure, keep improvements, and discard regressions.
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - AskUserQuestion
---
# AutoResearch: Autonomous Optimization Loop

Implements Karpathy's AutoResearch pattern for any measurable optimization target. You modify one thing, measure the result, keep it if improved, discard it if not, and repeat.

## Usage

Typical invocations:
- Claude Code: `/v1-autoresearch-skill [metric_command]`
- Codex: invoke `v1-autoresearch-skill` from the skills menu or use `$v1-autoresearch-skill [metric_command]`

Examples:
```text
/v1-autoresearch-skill
/v1-autoresearch-skill <metric_command>
```

In Codex, the slash examples below map directly to `$v1-autoresearch-skill ...`.

## How It Works

Three phases: **Setup**, **Loop**, **Debrief**.

---

## Phase 1: Setup

### 1.1 Collect Inputs

If the user did not provide arguments, collect these inputs interactively using AskUserQuestion:

**Required inputs:**
- **Asset path**: File or directory the agent is allowed to modify (e.g., `tests/`, `src/prompts/system.txt`, `webpack.config.js`)
- **Metric command**: A shell command that produces a single number on stdout. The agent will parse the last number from the output. Examples:
  - `pytest tests/ 2>&1 | tail -1` (parse time from pytest output)
  - `du -sb dist/ | cut -f1` (bundle size in bytes)
  - `hyperfine --runs 3 'node index.js' --export-json /dev/stdout | jq '.results[0].mean'`
- **Direction**: `lower` (lower is better, e.g., seconds, bytes, cost) or `higher` (higher is better, e.g., accuracy, pass rate)

**Optional inputs (with defaults):**
- **Constraint command**: A command that must exit 0 for any change to be kept. Default: none. Example: `pytest tests/ --tb=no -q` (all tests must pass)
- **Max cycles**: Maximum number of experiment cycles. Default: `50`
- **Time limit**: Maximum wall-clock minutes. Default: `120`
- **Metric runs**: How many times to run the metric command per measurement (takes median). Default: `3`

### 1.2 Validate Environment

Before starting the loop, verify all preconditions:

```
1. Confirm we are in a git repository: `git rev-parse --is-inside-work-tree`
2. Confirm working tree is clean: `git status --porcelain` should be empty
   - If dirty, ask user whether to stash or abort
3. Confirm asset path exists
4. Confirm metric command runs successfully and produces a parseable number
5. If constraint command provided, confirm it passes now (exit 0)
```

If any validation fails, report the failure clearly and stop. Do not start the loop with a broken setup.

### 1.3 Establish Baseline

Run the metric command {metric_runs} times. Take the **median** value. This is the BASELINE and also the initial BEST_KNOWN.

Display:

```
Baseline established: {BASELINE} ({direction})
Metric command: {metric_command}
Constraint: {constraint_command or "none"}
Asset: {asset_path}
Cycles: {max_cycles} | Time limit: {time_limit}min
```

### 1.4 Initialize Results Log

Create or append to `autoresearch-results.tsv` in the current working directory:

```
timestamp	cycle	change	metric_before	metric_after	verdict
```

### 1.5 Tag Baseline

```bash
git tag -f autoresearch-baseline
```

### 1.6 Read Strategy Reference

Read the strategy reference file for this skill:

```
${SKILL_DIR}/references/strategies.md
```

Use the strategies relevant to the current optimization target as a library of approaches to draw from during the loop. Prioritize high-impact strategies first.

---

## Phase 2: Loop

Repeat until a stop condition is met:

### 2.1 Analyze Current State

- Read the results log to see what has been tried and what worked/failed
- Read the asset to understand its current state
- Consult the strategy reference for untried approaches
- Pick the NEXT strategy to try based on:
  1. Expected impact (high to low)
  2. What hasn't been tried yet
  3. What related strategies worked in previous cycles

### 2.2 Make ONE Focused Change

Make exactly ONE modification to the asset. This is critical -- do not combine multiple changes in a single cycle. Isolating the variable is what makes the loop work.

Good changes:
- Change one fixture's scope from function to session
- Add pytest-xdist configuration
- Replace one expensive mock with a lighter alternative
- Remove one unnecessary import in test files

Bad changes (never do these):
- Change fixture scope AND add parallelization in one cycle
- Rewrite an entire file
- Make changes outside the asset path

### 2.3 Commit Before Verification

```bash
git add -A
git commit -m "autoresearch cycle {N}: {brief description of change}"
```

This commit happens BEFORE we know if the change helps. This is intentional -- it makes reverts clean.

### 2.4 Run Constraint Check (if configured)

Run the constraint command. If it exits non-zero:

```bash
git revert HEAD --no-edit
```

Log the result:
```
{timestamp}	{cycle}	{description}	{BEST_KNOWN}	CONSTRAINT_FAIL	DISCARDED
```

Skip to 2.8.

### 2.5 Measure New Metric

Run the metric command {metric_runs} times. Take the **median**. This is NEW_SCORE.

### 2.6 Compare and Decide

Compare NEW_SCORE to BEST_KNOWN respecting direction:

- **If direction=lower**: improved means NEW_SCORE < BEST_KNOWN
- **If direction=higher**: improved means NEW_SCORE > BEST_KNOWN

**If improved:**
- Update BEST_KNOWN = NEW_SCORE
- Log: `{timestamp} {cycle} {description} {old_best} {NEW_SCORE} KEPT`
- Display: `Cycle {N}: KEPT -- {description} ({old_best} -> {NEW_SCORE}, {improvement}%)`

**If NOT improved:**
```bash
git revert HEAD --no-edit
```
- Log: `{timestamp} {cycle} {description} {BEST_KNOWN} {NEW_SCORE} DISCARDED`
- Display: `Cycle {N}: DISCARDED -- {description} ({BEST_KNOWN} -> {NEW_SCORE}, no improvement)`

### 2.7 Display Running Summary

After every 5 cycles, display a brief progress summary:

```
--- Progress (cycle {N}/{max_cycles}) ---
Baseline: {BASELINE}
Current best: {BEST_KNOWN} ({improvement from baseline}%)
Kept: {kept_count} | Discarded: {discarded_count}
Time elapsed: {elapsed}min / {time_limit}min
---
```

### 2.8 Check Stop Conditions

Stop the loop if ANY of these are true:
1. Cycle count >= max_cycles
2. Elapsed wall-clock time >= time_limit minutes
3. Last 5 consecutive cycles were all DISCARDED (diminishing returns signal)
4. The user interrupts

---

## Phase 3: Debrief

### 3.1 Tag Final State

```bash
git tag -f autoresearch-final
```

### 3.2 Display Summary

```
========================================
AUTORESEARCH COMPLETE
========================================
Baseline:     {BASELINE}
Final best:   {BEST_KNOWN}
Improvement:  {improvement_pct}%
Cycles run:   {total_cycles}
Kept:         {kept_count}
Discarded:    {discarded_count}
Elapsed:      {elapsed_minutes}min
Results log:  autoresearch-results.tsv

KEPT CHANGES (in order):
1. {change_description} ({before} -> {after}, +{pct}%)
2. {change_description} ({before} -> {after}, +{pct}%)
...

Stop reason: {cycle limit | time limit | diminishing returns | user interrupt}
========================================
```

### 3.3 Suggest Next Steps

Based on results, suggest:
- If significant improvement: "Consider squashing the autoresearch commits into a single clean commit"
- If diminishing returns: "The easy wins are captured. Further improvement likely requires architectural changes outside the current asset scope"
- If constraint failures dominated: "Most changes broke the constraint. Consider narrowing the asset scope or relaxing the constraint"

---

## Guard Constraints

These are inviolable rules during the loop:

1. **NEVER modify this SKILL.md file** during an autoresearch run
2. **NEVER modify the results log format** during a run
3. **NEVER modify files outside the asset path** (except git operations and the results log)
4. **NEVER combine multiple changes in a single cycle** -- one change, one measurement, one decision
5. **NEVER skip the constraint check** -- if configured, it runs every cycle
6. **NEVER continue after a failed validation** in the setup phase

---

## Tips for Good Metric Commands

The metric command should:
- Produce a single number (the agent will parse the last number from stdout)
- Be deterministic enough that median-of-3 gives stable results
- Run in under 5 minutes (longer metrics slow the loop unacceptably)
- Not require user interaction

Examples:
```bash
# Pytest execution time (seconds)
/usr/bin/time -p pytest tests/ --tb=no -q 2>&1 | grep real | awk '{print $2}'

# Bundle size (bytes)
npm run build 2>/dev/null && du -sb dist/ | cut -f1

# Lighthouse performance score
lighthouse http://localhost:3000 --output=json --quiet | jq '.categories.performance.score * 100'

# Python script execution time
/usr/bin/time -p python3 script.py 2>&1 | grep real | awk '{print $2}'

# Test count (if optimizing for fewer tests while maintaining coverage)
pytest --collect-only -q 2>/dev/null | tail -1 | grep -oP '\d+'
```
