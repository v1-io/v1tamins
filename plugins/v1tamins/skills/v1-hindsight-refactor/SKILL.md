---
name: v1-hindsight-refactor
description: Use when a first-pass fix works but is exploratory, messy, or overbuilt, and you want to delete it and reimplement a better version using what the first pass taught you. Triggers on "delete your fix and implement a better version", "hindsight refactor", "second pass refactor", "second pass rewrite", "rewrite after exploration", and "clean reimplementation".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Hindsight Refactor

Use the first implementation as reconnaissance, not as the final answer.

## Usage

Typical invocations:
- Claude Code: `/v1-hindsight-refactor`
- Codex: invoke `v1-hindsight-refactor` from the skills menu or use `$v1-hindsight-refactor`

Examples:
```bash
/v1-hindsight-refactor
/v1-hindsight-refactor src/summarizer.py
```

In Codex, the slash examples below map directly to `$v1-hindsight-refactor ...`.

## When To Use It

Use this skill when:
- the first pass fixed the bug but added too much code
- the agent had to explore several dead ends to understand the problem
- the final diff feels correct but clunky
- you want a more concise, elegant, or idiomatic implementation

Do not use this skill when:
- the first pass is already simple and idiomatic
- the area is too risky to delete without a strong verification harness
- the code is exploratory by nature and readability is not the bottleneck

## Process

### 1. Treat the first pass as reconnaissance
Extract what the first pass learned before changing anything:
- the actual root cause
- invariants that must hold
- edge cases that matter
- tests or repros that prove the fix
- repo patterns the final code should match

Write these down briefly in working notes if the problem is subtle.

### 2. Preserve the proof
Keep or add the smallest verification harness that protects the behavior:
- failing test
- reliable repro steps
- targeted script
- before/after output check

Do not delete the exploratory implementation until there is a way to prove the rewrite still works.

### 3. Delete the exploratory fix mentally, then structurally
Do not polish the exploratory code line by line.
Instead:
- step back to the smallest correct design
- remove speculative helpers and defensive clutter
- reimplement from the learned constraints
- prefer the shape a strong human would have written first

### 4. Optimize for clarity, not cleverness
Prefer:
- fewer moving parts
- direct control flow
- existing repo idioms
- explicit names
- local helpers over broad abstractions

Avoid:
- preserving unnecessary scaffolding from the first pass
- keeping abstractions created only to support dead ends
- “smart” rewrites that are shorter but harder to read

### 5. Compare the rewrite against the first pass
Check whether the new version is:
- smaller or simpler
- easier to explain
- equally correct on the same verification harness
- closer to surrounding code style

If the rewrite is not meaningfully better, keep the first pass.

## Output

Report in 2 parts:

```markdown
## Learned from first pass
- Root cause: ...
- Key constraints: ...

## Rewrite result
- Reimplemented with [simpler structure]
- Verification: [tests/repro]
- Why this is better: [one short reason]
```

## Guidelines

- Preserve behavior unless the user asked for behavior changes.
- Keep the verification harness until the rewrite passes.
- Match local codebase style over abstract purity.
- If the first pass exposed ambiguity, resolve the ambiguity before rewriting.
- If the first pass is already the cleanest implementation, say so and stop.
