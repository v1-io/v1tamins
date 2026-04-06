---
name: code-review
description: "Use when reviewing a pull request, posting code review feedback to GitHub, or auditing PR changes for correctness and security. Triggers on 'review this PR', 'code review', 'check this pull request', 'audit PR', 'review changes'."
allowed-tools: "Bash, Read, Grep"
---

# Code Review

Performs a staff-level PR review using full repo context, then posts the review to GitHub via `gh`.

## Usage

```
/code-review <PR_URL_or_NUMBER>
```

## Workflow

### 1. Gather PR Context

Fetches PR metadata and comments to understand scope and risk:

```bash
gh pr view <PR> --json title,body,author,baseRefName,headRefName,commits,files,labels,additions,deletions
gh pr view <PR> --comments
gh pr diff <PR>
```

Extracts what the PR does, which services it touches, and risk flags (auth, migrations, concurrency, data integrity).

### 2. Build Repo-Aware Understanding

For each changed file, reads surrounding code (imports, callers, contracts) and searches for usage patterns with `rg "<Symbol>" -n` to align with project architecture.

### 3. Review Systematically

Evaluates each area and flags issues by severity (Critical/Medium/Low/Nit):

- **Correctness**: Boundary cases, idempotency, error paths
- **Concurrency**: No blocking in async contexts; prefer `.ainvoke()` over `.invoke()` for LangChain
- **Security**: No hardcoded secrets, input validation, no PII in logs
- **Performance**: No N+1 or unbounded queries
- **Observability**: Logging conventions followed
- **Migrations**: Models registered, `updated_at` updated, safe migrations
- **Tests**: Cover the "why", no flaky patterns

### 4. Post Review to GitHub

Posts a summary comment with confidence score (1-5), file-level confidence table, and a Mermaid diagram for non-trivial flows:

```bash
gh pr review <PR> --comment -b "<BODY>"
# Or for must-fix issues:
gh pr review <PR> --request-changes -b "<BODY>"
```

Then posts per-file inline comments with actionable suggestions:

```bash
gh issue comment <PR_URL> --body "<BODY>"
```

## Confidence Scoring

| Score | Meaning |
|-------|---------|
| 5/5 | Trivial change, well-tested, no risk |
| 4/5 | Standard change, good coverage, minor concerns |
| 3/5 | Non-trivial, needs attention in specific areas |
| 2/5 | Significant concerns, missing tests, risky patterns |
| 1/5 | Likely bugs, security issues, or major problems |

Reduce score for: migrations, auth/permissions, concurrency, broad refactors, missing tests.
