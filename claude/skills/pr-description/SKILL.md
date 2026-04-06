---
name: pr-description
description: "Use when generating a pull request description, updating an existing PR body on GitHub, or summarizing branch changes for a PR. Triggers on 'write PR description', 'update PR body', 'describe this PR', 'generate PR summary', 'PR description'."
allowed-tools: "Bash, Read, Grep"
---

# Generate PR Description

Analyzes the diff between the current branch and `main`, then generates and posts a comprehensive PR description to GitHub via `gh pr edit`.

## Usage

```
/pr-description <PR_URL_or_NUMBER>
```

## Workflow

### 1. Analyze Changes

Gathers the full picture of what changed and why:

```bash
git diff main HEAD              # What changed
git log main..HEAD --oneline    # Commit history
```

### 2. Generate Description

Produces a structured PR description:
- **Title**: Concise, max 72 characters
- **Summary**: What the PR accomplishes and why
- **Changes Made**: Key modifications, highlights breaking changes
- **Testing**: How changes were tested, new test cases added
- **Related Issues**: Links to relevant issues or tickets

### 3. Update GitHub

Posts the description directly to the PR:

```bash
gh pr edit <PR_NUMBER> --title "<TITLE>" --body "<BODY>"
```

Falls back to displaying the description for manual copy/paste if `gh` CLI is unavailable.

## Notes

- Requires `gh` CLI installed and authenticated
- Automatically extracts PR number from URLs
- Breaking changes are highlighted prominently
