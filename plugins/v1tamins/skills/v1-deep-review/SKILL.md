---
name: v1-deep-review
description: Use when reviewing a PR or branch for merge risk or maintainability. Triggers on "review this PR", "code review", or "maintainability audit".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Skill
---
# Deep Review

Review any pull request, branch, or change — code, docs, config, or mixed — on two bars:

- **Merge risk:** is it correct, complete, and safe to merge? Bugs, regressions, missing requirements, security, data, tests, scope drift.
- **Structural maintainability:** does it leave the codebase simpler to change? Abstraction quality, spaghetti/branching growth, file-size boundaries, type/ownership cleanliness.

Default mode is review-only. Apply fixes only when the user explicitly asks for "review and fix", "fix review findings", or a shipping workflow clearly requested code changes.

## Usage

Typical invocations:
- Claude Code: `/v1-deep-review <PR_URL_or_NUMBER>` or `/v1-deep-review` to review the current branch
- Codex: invoke `v1-deep-review` from the skills menu or use `$v1-deep-review <PR_URL_or_NUMBER>`

Examples:
```bash
/v1-deep-review https://github.com/your-org/your-repo/pull/123
/v1-deep-review 123
/v1-deep-review
/v1-deep-review --post
/v1-deep-review --fix
```

For a multi-agent review across peer runtimes, use `v1-review-board`. To respond to review comments already posted on a PR, use `v1-address-review`.

## Operating Rules

- Lead with findings, ordered by severity. Keep summaries secondary.
- Cite exact `file_path:line_number` for every finding.
- Review the full diff before commenting. Do not flag issues already fixed elsewhere in the same diff.
- Only report real, actionable problems. Skip style preferences unless they hide a bug or maintainability risk.
- Verify claims by reading code. Do not say "probably", "likely handled", or "should be fine" without evidence.
- Do not post to GitHub unless the user used `--post`, explicitly asked to post, or the existing workflow clearly expects posting. Otherwise return review text in chat.
- Do not modify code in default review mode.

## The Two Bars

Both bars run by default on code changes. Steps 1-5 below establish context and cover the **merge-risk** bar. Step 6 applies the **structural** bar. For a pure docs/config PR, run the merge-risk bar adapted (correctness, completeness vs intent, broken links/refs, cross-doc consistency) and skip the structural bar.

If the user's request is explicitly and only about structure ("maintainability audit", "architecture review"), lead with the structural bar but still sanity-check merge risk. If it is explicitly and only about merge risk ("review for bugs before merge"), lead with merge risk and apply structure as a secondary lens.

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

Extract what the work claims to do from the PR title/body, commit messages, branch name, `TODOS.md`, recent files in `docs/plans/` or `docs/brainstorms/`, and any Linear/Jira references. Produce a one-line intent summary before reviewing:

```markdown
Intent: <what this branch appears to be trying to accomplish>
Changed surface: <main files/modules touched>
Risk flags: <auth/data/API/async/UI/migrations/external services/tests/docs>
```

### 3. Scope Drift And Completion Audit

Compare stated intent against the diff. Check for scope creep (unrelated refactors, unmentioned behavior, files outside the expected surface), missing requirements, partial implementation (code not wired, tests without production code, UI without backend or vice versa), and test gaps.

If a plan file is found, classify each actionable item as `[DONE]` / `[PARTIAL]` / `[NOT DONE]` / `[CHANGED]`. Keep this audit concise — informational unless a missing item causes a real bug or user-facing gap.

### 4. Build Repo-Aware Understanding

For each meaningful changed file: read surrounding code, imports, callers, and contracts; search repo-wide for usage (`rg "<Symbol>" -n`); read nearby tests and fixtures; check `AGENTS.md`, `CLAUDE.md`, README, and local docs. Align findings with existing patterns before proposing new abstractions.

### 5. Merge-Risk Passes

Run these as lenses, not separate reports.

**Always run:**
- **Correctness:** logic errors, boundary cases, state transitions, idempotency, error propagation
- **Testing:** missing negative-path tests, edge cases, isolation, flakiness, weak assertions
- **Maintainability (surface):** dead code, stale comments, unnecessary abstractions, duplicated logic, unclear naming (deep structural review is step 6)

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

Use the matrix to catch half-wired work. After the passes, do one adversarial pass:

> Think like an attacker, a chaos engineer, and a hostile QA tester. What fails under load, bad input, retries, concurrency, stale state, partial failure, or confused users?

### 6. Structural Pass

For code changes, apply the structural maintainability bar. **Load [references/structural-review.md](references/structural-review.md)** and use it as a lens: does the change leave the codebase simpler to change, or add avoidable concepts, branches, files, casts, wrappers, and ownership leaks? It carries the deep-module / code-judo rubric, the >1000-line file blocker, "define errors out of existence", the structural finding shape, and the structural approval bar. Skip for pure docs/config PRs.

### 7. Finding Gates

Severity: **Critical** (likely production bug, security, data loss, broken core flow, unsafe migration, or a structural regression that will force a costly rewrite) · **High** (serious edge case, regression, missing required behavior, or file-size/spaghetti explosion) · **Medium** (maintainability/test/UX gap that can cause future bugs) · **Low/Nit** (minor, clearly actionable, low-noise only).

Confidence gates: 4-5/5 include in main findings; 3/5 include only with explicit uncertainty; 1-2/5 do not include.

Merge-risk findings use this shape:
```markdown
[Severity] file_path:line_number - Short title
Problem: What is wrong and when it fails.
Impact: Why it matters.
Fix: Concrete change to make.
Test: Specific test or verification to add/run.
Confidence: N/5.
```

Structural findings use the shape in `references/structural-review.md`. If no issues are found, say so clearly and mention residual risk or unverified areas.

### 8. Fix-First Mode

Only when the user explicitly asks to fix findings. Classify: **AUTO-FIX** (mechanical, local, low-risk, no product judgment) vs **ASK** (behavior change, architecture choice, migration, public API change, security-sensitive, broad refactor, or uncertain). Apply AUTO-FIX items with `Edit`, then report `[AUTO-FIXED] file_path:line_number - Problem -> fix applied`. Batch ASK items in one concise question. Do not commit, push, or create PRs from this skill.

If tests are already failing, invoke or recommend `v1-fix-tests`. If the issue is missing coverage, invoke or recommend `v1-write-tests` after the user approves adding tests.

### 9. Output

```markdown
## Findings

<severity-ordered findings across both bars, or "No findings.">

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

### 10. Posting To GitHub

When posting is requested:

1. If any Critical or High findings remain, request changes.
2. Otherwise post a comment review.
3. Post only high-confidence findings. Do not post speculative notes.
4. Prefer one consolidated review body over many noisy comments unless line-level comments are specifically useful.

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
- Do not list every possible improvement. Review for merge risk and genuine structural regressions.
- Do not ask for large refactors unless the current change creates real risk or a clear structural regression.
- Do not request tests without naming the behavior that must be protected.
- Do not leave vague comments like "consider handling errors" without a concrete failure mode.
- Do not soften a major maintainability regression into a mild suggestion.
- Do not post secrets, private logs, or sensitive data in GitHub comments.
