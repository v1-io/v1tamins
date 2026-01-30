---
name: address-review
description: Use when addressing PR review comments from Copilot, bots, or humans. Triggers on "fix review comments", "address Copilot feedback", "respond to PR comments".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# Address PR Review Comments

Fetch code review comments on a PR (from Copilot, bots, or humans), critically evaluate each one, fix the valid issues, and reply to each comment.

## Usage

```
/address-review <PR_URL_or_NUMBER>
```

**Examples:**
```bash
/address-review https://github.com/your-org/your-repo/pull/123
/address-review 123
```

## What It Does

### 1. Fetch Review Comments
Checks **BOTH** types of comments:
- **Line-specific review comments**: `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --paginate`
- **General PR-level comments**: `gh api repos/{owner}/{repo}/issues/{pr_number}/comments --paginate`

Uses jq queries to find unreplied comments:
```bash
# Unreplied line-specific comments
gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate | \
jq -r '[.[] | select(.in_reply_to_id == null)] as $originals |
       [.[] | .in_reply_to_id] as $replied_ids |
       $originals | map(select(.id as $id | $replied_ids | index($id) | not))'

# General PR comments (review-style)
gh api repos/{owner}/{repo}/issues/{pr}/comments --paginate | \
jq -r '.[] | select(.body | test("^###? Review:"; "i"))'
```

### 2. Analyze Each Comment
For each unreplied comment:
- Reads the relevant file and code section
- Critically evaluates if suggestion is:
  - **Valid**: Issue is real, should be fixed
  - **Invalid**: False positive, not applicable
  - **Partial**: Issue valid but fix needs adjustment

### 3. Fix Valid Issues
- For valid comments: implements fix following existing patterns
- For partial: implements appropriate fix addressing the concern
- Documents why invalid comments are skipped

### 4. Reply to Each Comment
- **Line-specific**: `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body="..."`
- **General PR-level**: Summary comment via `gh api repos/{owner}/{repo}/issues/{pr}/comments`

Replies are brief:
- Valid: "Fixed ✅" or "Fixed - [note if approach differs]"
- Invalid: "Skipped - [brief reason]"
- Partial: "Addressed - [note on approach]"

### 5. Commit and Push
Commits all fixes with descriptive message and pushes.

## Evaluation Criteria

- **Unused imports**: Usually valid - remove them
- **Duplicate function calls**: Usually valid - cache results
- **Performance suggestions**: Evaluate if impact is meaningful
- **Documentation updates**: Valid if docs outdated
- **Test mock updates**: Valid if mocks don't match implementation
- **Refactoring suggestions**: Evaluate against KISS/YAGNI
- **Security suggestions**: Take seriously, verify vulnerability is real

## Output

Summary table of all comments addressed:

| # | File:Line | Issue | Action | Reply |
|---|-----------|-------|--------|-------|
| 1 | path.py:42 | Unused import | Fixed | ✅ |
| 2 | test.py:100 | Incorrect mock | Fixed | ✅ |
| 3 | utils.py:50 | Suggested refactor | Skipped | Not needed per YAGNI |
