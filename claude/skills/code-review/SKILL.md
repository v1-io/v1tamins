---
name: code-review
description: Use when reviewing a PR or posting code review feedback to GitHub. Triggers on "review this PR", "code review", "check this pull request".
allowed-tools:
  - Bash
  - Read
  - Grep
---

# Code Review (PR-Based, Elite/Rigorous)

Perform a **staff-level PR review** using full repo context, then **post the review to GitHub**.

## Usage

```
/code-review <PR_URL_or_NUMBER>
```

**Examples:**
```bash
/code-review https://github.com/your-org/your-repo/pull/123
/code-review 123
```

## What It Does

### 1. Gather PR Context
```bash
gh pr view <PR> --json title,body,author,baseRefName,headRefName,commits,files,labels,additions,deletions
gh pr view <PR> --comments
```

Extracts:
- **What** the PR claims to do (title/body/commits)
- **Where** it touches (services, shared libs, frontend)
- **Risk flags**: auth, migrations, background jobs, concurrency, data integrity

### 2. Get the Diff
```bash
gh pr diff <PR>           # Full diff
gh pr diff <PR> --name-only # File list
```

### 3. Build Repo-Aware Understanding
For each meaningful changed file:
- Reads surrounding code (imports, callers, contracts)
- Searches repo-wide for usage patterns: `rg "<Symbol>" -n`
- Aligns with project architectural patterns

### 4. Review Systematically

**Correctness & Logic:**
- Boundary cases, idempotency, error paths

**Concurrency & Async:**
- No blocking calls in async contexts
- LangChain/LangGraph: prefer `.ainvoke()` over `.invoke()`

**Security & Privacy:**
- No hardcoded secrets, input validation, no PII in logs

**Performance & Cost:**
- No N+1 queries, no unbounded queries

**Observability:**
- Logging conventions followed

**Database/Migrations:**
- Models registered, `updated_at` updated, safe migrations

**Tests:**
- Cover the "why", no flaky patterns

### 5. Produce Outputs

**Output A: Main Summary Comment**
- PR Summary (3-6 bullets)
- Key Findings (severity-ranked: Critical/Medium/Low/Nit)
- **Confidence Score** (X/5 with reasoning)
- **File-level confidence table**
- **Mermaid sequence diagram** (if non-trivial)

Posted via:
```bash
gh pr review <PR> --comment -b "<BODY>"
# Or for must-fix issues:
gh pr review <PR> --request-changes -b "<BODY>"
```

**Output B: Per-File Comments**
One comment per file with actionable suggestions:
```markdown
### Review: `path/to/file` (Importance: Medium)

- **Issue**: <short title>
- **Why it matters**: <tie to project patterns>
- **Suggested change**: <what to do>
- **Test**: <test to add if applicable>
```

Posted via:
```bash
gh issue comment <PR_URL> --body "<BODY>"
```

## Confidence Scoring Guide

- **5/5**: Trivial change, well-tested, no risk
- **4/5**: Standard change, good coverage, minor concerns
- **3/5**: Non-trivial change, needs attention in specific areas
- **2/5**: Significant concerns, missing tests, risky patterns
- **1/5**: Likely bugs, security issues, or major problems

Reduce score for: migrations, auth/permissions, concurrency, broad refactors, missing tests.
