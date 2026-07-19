# Hindsight mode

Use the first implementation as reconnaissance, not as the final answer. Do not polish the exploratory code line by line.

## When To Use

Use hindsight mode when:
- the first pass fixed the bug but added too much code
- the agent had to explore several dead ends to understand the problem
- the final diff feels correct but clunky
- the user wants a more concise, elegant, or idiomatic implementation

Do not use when:
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

- Step back to the smallest correct design
- Remove speculative helpers and defensive clutter
- Reimplement from the learned constraints
- Prefer the shape a strong human would have written first

### 4. Optimize for clarity, not cleverness

Prefer fewer moving parts, direct control flow, existing repo idioms, explicit names, and local helpers over broad abstractions.

Avoid preserving unnecessary scaffolding from the first pass, keeping abstractions created only to support dead ends, or “smart” rewrites that are shorter but harder to read.

### 5. Compare the rewrite against the first pass

Check whether the new version is smaller or simpler, easier to explain, equally correct on the same verification harness, and closer to surrounding code style. If the rewrite is not meaningfully better, keep the first pass.

## Output

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
- If the first pass exposed ambiguity, resolve it before rewriting.
- If the first pass is already the cleanest implementation, say so and stop.
