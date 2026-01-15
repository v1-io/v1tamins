# Address PR Review Comments

## Overview

Fetch code review comments on a PR (from Copilot, bots, or humans), critically evaluate each one, fix the valid issues, and reply to each comment with a brief response.

## Input

Provide the PR number or full GitHub PR URL as part of your prompt, e.g.:
- `/address-copilot-review 588`
- `/address-copilot-review https://github.com/v1-io/abi/pull/588`

## Steps

1. **Fetch Review Comments**
   - **IMPORTANT**: Check BOTH types of comments:
     - **Line-specific review comments**: `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --paginate`
     - **General PR-level comments**: `gh api repos/{owner}/{repo}/issues/{pr_number}/comments --paginate`
   - Parse the PR URL/number to extract owner, repo, and PR number
   - **Find unreplied line-specific comments** using this jq query:
     ```bash
     gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --paginate | \
     jq -r '[.[] | select(.in_reply_to_id == null)] as $originals |
            [.[] | .in_reply_to_id] as $replied_ids |
            $originals | map(select(.id as $id | $replied_ids | index($id) | not)) |
            map({id: .id, path: .path, line: .line, user: .user.login, body: .body}) | .[]'
     ```
   - **Find unreplied general PR comments** (look for review-style comments from reviewers):
     ```bash
     gh api repos/{owner}/{repo}/issues/{pr_number}/comments --paginate | \
     jq -r '.[] | select(.body | test("^###? Review:"; "i")) |
            {id: .id, user: .user.login, created_at: .created_at, body: .body[0:500]}'
     ```
   - These filters help find original comments (not replies) that don't have replies yet

2. **Analyze Each Comment**
   - **IMPORTANT**: Check both line-specific AND general PR-level comments
   - Don't manually scan - use the jq queries to systematically find ALL unreplied comments
   - For each unreplied comment:
     - Read the relevant file and code section
     - Critically evaluate if the suggestion is:
       - **Valid**: The issue is real and should be fixed
       - **Invalid**: False positive, not applicable, or would cause other issues
       - **Partial**: The issue is valid but the suggested fix needs adjustment

3. **Fix Valid Issues**
   - For valid comments, implement the fix following existing code patterns
   - For partial issues, implement an appropriate fix that addresses the underlying concern
   - Skip invalid comments but document why they're being skipped

4. **Reply to Each Comment**
   - **For line-specific comments**: Use `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies -f body="..."`
   - **For general PR-level comments**: Post a summary as a new issue comment with `gh api repos/{owner}/{repo}/issues/{pr_number}/comments -f body="..."`
   - Keep replies brief and professional:
     - Valid: "Fixed ✅" or "Fixed - [brief note if approach differs]"
     - Invalid: "Skipped - [brief reason]"
     - Partial: "Addressed - [brief note on approach taken]"
   - For multiple general comments, create a single summary comment listing all fixes

5. **Commit and Push**
   - Commit all fixes with a descriptive message referencing the PR review
   - Push to the branch

## Example Workflow

```bash
# Step 1a: Find all unreplied line-specific review comments
gh api repos/v1-io/abi/pulls/588/comments --paginate | \
jq -r '[.[] | select(.in_reply_to_id == null)] as $originals |
       [.[] | .in_reply_to_id] as $replied_ids |
       $originals | map(select(.id as $id | $replied_ids | index($id) | not))'

# Step 1b: Find general PR-level review comments
gh api repos/v1-io/abi/issues/588/comments --paginate | \
jq -r '.[] | select(.body | test("^###? Review:"; "i")) |
       {id: .id, user: .user.login, body: .body[0:300]}'

# Step 2: Read the file and evaluate each comment
# (use read_file tool to check the code)

# Step 3a: Reply to a line-specific comment (after fixing or deciding to skip)
gh api repos/v1-io/abi/pulls/588/comments/12345/replies -f body="Fixed ✅"

# Step 3b: Reply to general comments with a summary
gh api repos/v1-io/abi/issues/588/comments -f body="## Addressed Review Comments

All 8 review comments have been addressed:
1. ✅ file.py - Fixed duplicate parameter
2. ✅ test.py - Updated test expectations
..."

# Step 4: Verify all line-specific comments are addressed
gh api repos/v1-io/abi/pulls/588/comments --paginate | \
jq -r '[.[] | select(.in_reply_to_id == null)] as $originals |
       [.[] | .in_reply_to_id] as $replied_ids |
       $originals | map(select(.id as $id | $replied_ids | index($id) | not)) | length'
# Should return 0 when all comments have replies
```

## Evaluation Criteria

When evaluating suggestions, consider:

- **Unused imports**: Usually valid - remove them
- **Duplicate function calls**: Usually valid - cache results in a variable
- **Performance suggestions**: Evaluate if the performance impact is meaningful
- **Documentation updates**: Valid if docs are outdated
- **Test mock updates**: Valid if mocks don't match current implementation
- **Refactoring suggestions**: Evaluate against KISS/YAGNI principles
- **Security suggestions**: Take seriously, but verify the vulnerability is real

## Important Notes

- **Two types of comments**: Always check BOTH line-specific review comments (`/pulls/{pr}/comments`) AND general PR-level comments (`/issues/{pr}/comments`)
- **Multiple review sessions**: Reviewers may comment multiple times, so use `--paginate` to get all comments
- **Always verify**: After replying to all comments, run the verification query to ensure count is 0
- **Systematic approach**: Use the provided jq queries rather than manually scanning output to avoid missing comments
- **General comments**: Self-review comments often appear as general PR comments starting with "Review:" rather than line-specific comments

## Output

Provide a summary table of all comments addressed:

| # | File:Line | Issue | Action | Reply |
|---|-----------|-------|--------|-------|
| 1 | path.py:42 | Unused import | Fixed | ✅ |
| 2 | test.py:100 | Incorrect mock | Fixed | ✅ |
| 3 | utils.py:50 | Suggested refactor | Skipped | Not needed per YAGNI |
