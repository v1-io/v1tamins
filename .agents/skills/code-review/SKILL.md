---
name: code-review
description: Use when reviewing a PR, reviewing the current branch, or posting code review feedback to GitHub. Triggers on "review this PR", "code review", "check this pull request", "review my branch", "review and fix".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Skill
---

# Code Review

Perform a staff-level code review using repo context, stated intent, and the actual diff. Prioritize bugs, regressions, missing requirements, security risks, data issues, and test gaps.

Default mode is review-only. Apply fixes only when the user explicitly asks for "review and fix", "fix review findings", or a shipping workflow clearly requested code changes.

## Usage

Typical invocations:
- Claude Code: `/code-review <PR_URL_or_NUMBER>`
- Claude Code: `/code-review` to review the current branch
- Codex: invoke `code-review` from the skills menu or use `$code-review <PR_URL_or_NUMBER>`

Examples:
```bash
/code-review https://github.com/your-org/your-repo/pull/123
/code-review 123
/code-review
/code-review --post
/code-review --fix
```

In Codex, the slash examples below map directly to `$code-review ...`.

## Operating Rules

- Lead with findings, ordered by severity. Keep summaries secondary.
- Cite exact `file_path:line_number` for every finding.
- Review the full diff before commenting. Do not flag issues already fixed elsewhere in the same diff.
- Only report real, actionable problems. Skip style preferences unless they hide a bug or maintainability risk.
- Verify claims by reading code. Do not say "probably", "likely handled", or "should be fine" without evidence.
- Do not post to GitHub unless the user used `--post`, explicitly asked to post, or the existing workflow clearly expects posting. Otherwise return review text in chat.
- Do not modify code in default review mode.

## Workflow

### 1. Resolve Target

Determine whether the target is a PR or the current branch.

For a PR argument:
```bash
gh pr view <PR> --json title,body,author,baseRefName,headRefName,commits,files,labels,additions,deletions
gh pr view <PR> --comments
gh pr diff <PR> --name-only
gh pr diff <PR>
```

For the current branch:
```bash
git status --short
git branch --show-current
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
BASE_BRANCH=${BASE_BRANCH:-main}
git diff --name-only origin/$BASE_BRANCH...HEAD
git diff origin/$BASE_BRANCH...HEAD
git log --oneline origin/$BASE_BRANCH..HEAD
```

If the default branch is not available locally, fetch it before reviewing. Never use destructive git commands.

### 2. Establish Stated Intent

Extract what the work claims to do from:
- PR title/body
- Commit messages
- Branch name
- `TODOS.md`, if present
- Recent relevant files in `docs/plans/` or `docs/brainstorms/`, if present
- Linear/Jira ticket references in the branch, commits, or PR body, if accessible

Produce a one-line intent summary before reviewing:

```markdown
Intent: <what this branch appears to be trying to accomplish>
Changed surface: <main files/modules touched>
Risk flags: <auth/data/API/async/UI/migrations/external services/tests/docs>
```

### 3. Scope Drift And Completion Audit

Before code quality review, compare stated intent against the diff.

Check for:
- Scope creep: unrelated refactors, new behavior not mentioned, files outside the expected surface
- Missing requirements: stated work not present in the diff
- Partial implementation: code started but not wired, tests added without production code, UI without backend, backend without user path
- Test gaps for stated requirements

If a plan file is found, extract actionable items and classify each as:

```markdown
[DONE]      Clear evidence in diff
[PARTIAL]   Some evidence, incomplete
[NOT DONE]  No evidence
[CHANGED]   Different implementation, same goal achieved
```

Keep this audit concise. It is informational unless a missing item causes a real bug or user-facing gap.

### 4. Build Repo-Aware Understanding

For each meaningful changed file:
- Read surrounding code, imports, callers, and contracts.
- Search repo-wide for usage patterns: `rg "<Symbol>" -n`.
- Read nearby tests and fixtures.
- Check project instructions in `AGENTS.md`, `CLAUDE.md`, README, and local docs.
- Align findings with the project's existing patterns before proposing new abstractions.

### 5. Specialist Passes

Run these passes in the main review. Use them as lenses, not as separate reports.

**Always run:**
- **Correctness:** logic errors, boundary cases, state transitions, idempotency, error propagation
- **Testing:** missing negative-path tests, edge cases, isolation, flakiness, weak assertions
- **Maintainability:** dead code, stale comments, unnecessary abstractions, duplicated logic, unclear naming

**Run when applicable:**
- **Security:** auth/authz, input validation, secrets, injection, SSRF, unsafe rendering
- **Data/migrations:** rollback safety, data loss, locking, backfills, indexes, mixed-version deploys
- **Performance:** N+1 queries, unbounded loops/queries, algorithmic complexity, bundle size, blocking I/O
- **API contracts:** response shape changes, status codes, versioning, pagination, webhook payloads
- **Frontend/UI:** async races, loading/error/empty states, accessibility, responsive behavior, console errors
- **External services/LLM:** trust boundaries, schema validation, retries, timeouts, rate limits, cost controls

When a UI change crosses an API, service client, state hook, or server route boundary, build a contract matrix before writing findings:

| Layer | File(s) | Contract to verify | Tests/evidence |
| --- | --- | --- | --- |
| API route or handler | `...` | auth, status codes, request/response shape, pagination, timeout/abort behavior | `...` |
| Service client | `...` | typed inputs/outputs, error mapping, retry/abort behavior | `...` |
| State hook/store | `...` | loading, empty, stale, error, optimistic update, cancellation | `...` |
| Component/view | `...` | rendered states, accessibility, responsive layout, destructive-action affordances | `...` |

Use the matrix to catch half-wired work: backend without user path, UI without backend contract, service-client type drift, missing empty/error states, or tests that cover only one layer.

After specialist passes, do one adversarial pass:

> Think like an attacker, a chaos engineer, and a hostile QA tester. What fails under load, bad input, retries, concurrency, stale state, partial failure, or confused users?

### 6. Finding Gates

Use this severity model:

- **Critical:** likely production bug, security issue, data loss/corruption, broken core flow, unsafe migration
- **High:** serious edge case, regression, missing required behavior, unreliable deploy/runtime behavior
- **Medium:** meaningful maintainability, test, or UX gap that can cause future bugs
- **Low/Nit:** minor issue. Include only when clearly actionable and low-noise.

Use confidence gates:
- 4-5/5: include in main findings
- 3/5: include only with explicit uncertainty and verification needed
- 1-2/5: do not include

For each finding, include:

```markdown
[Severity] file_path:line_number - Short title
Problem: What is wrong and when it fails.
Impact: Why it matters.
Fix: Concrete change to make.
Test: Specific test or verification to add/run.
Confidence: N/5.
```

If no issues are found, say that clearly and mention residual risk or unverified areas.

### 7. Fix-First Mode

Only enter this mode when the user explicitly asks to fix findings.

Classify findings:
- **AUTO-FIX:** mechanical, local, low-risk, clearly correct, no product judgment needed
- **ASK:** behavior change, architecture choice, data migration, public API change, security-sensitive change, broad refactor, or uncertain fix

Apply AUTO-FIX items directly with `Edit`, then report:

```markdown
[AUTO-FIXED] file_path:line_number - Problem -> fix applied
```

Batch ASK items in one concise question with recommended choices. Do not commit, push, or create PRs from this skill.

If tests are already failing, invoke or recommend `fix-tests` instead of trying to fold a full test repair loop into the review. If the issue is missing coverage, invoke or recommend `write-tests` after the user approves adding tests.

### 8. Output

Return this structure:

```markdown
## Findings

<severity-ordered findings, or "No findings.">

## Open Questions

<only questions that affect review confidence or implementation safety>

## Scope Check

Intent: ...
Delivered: ...
Drift/missing work: ...

## Verification

Tests/checks reviewed or run:
- ...

Residual risk:
- ...
```

Keep the final summary short. Findings are the product.

### 9. Posting To GitHub

When posting is requested:

1. If any Critical or High findings remain, request changes.
2. Otherwise post a comment review.
3. Post only high-confidence findings. Do not post speculative notes.
4. Prefer one consolidated review body over many noisy comments unless line-level comments are specifically useful.

```markdown
## Code Review

### Findings
...

### Scope Check
...

### Verification
...
```

```bash
gh pr review <PR> --request-changes -b "$(cat /tmp/review.md)"
gh pr review <PR> --comment -b "$(cat /tmp/review.md)"
```

## Confidence Scoring Guide

- **5/5**: Trivial change, well-tested, no risk
- **4/5**: Standard change, good coverage, minor concerns
- **3/5**: Non-trivial change, needs attention in specific areas
- **2/5**: Significant concerns, missing tests, risky patterns
- **1/5**: Likely bugs, security issues, or major problems

Reduce score for: migrations, auth/permissions, concurrency, broad refactors, missing tests.

## Anti-Patterns

- Do not rubber-stamp because CI passes.
- Do not list every possible improvement. Review for merge risk.
- Do not ask for large refactors unless the current change creates real risk.
- Do not request tests without naming the behavior that must be protected.
- Do not leave vague comments like "consider handling errors" without a concrete failure mode.
- Do not post secrets, private logs, or sensitive data in GitHub comments.
