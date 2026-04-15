---
name: address-review
description: Use when addressing PR review comments from Copilot, Code Factory, bots, or humans. Triggers on "fix review comments", "address review feedback", "address code factory", "respond to PR comments".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# Address PR Review Comments

Fetch code review comments on a PR (from Copilot, Code Factory, bots, or humans), critically evaluate each one, fix the valid issues, and reply to each comment.

## Usage

Typical invocations:
- Claude Code: `/address-review <PR_URL_or_NUMBER>`
- Codex: invoke `address-review` from the skills menu or use `$address-review <PR_URL_or_NUMBER>`

Examples:
```bash
/address-review https://github.com/your-org/your-repo/pull/123
/address-review 123
```

In Codex, the slash examples below map directly to `$address-review ...`.

## What It Does

### 1. Fetch Review Comments
Checks **three** sources of review feedback:

#### A. Line-specific review comments
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate | \
jq -r '[.[] | select(.in_reply_to_id == null)] as $originals |
       [.[] | .in_reply_to_id] as $replied_ids |
       $originals | map(select(.id as $id | $replied_ids | index($id) | not))'
```

#### B. General PR-level comments (Copilot, humans)
```bash
gh api repos/{owner}/{repo}/issues/{pr}/comments --paginate | \
jq -r '.[] | select(.body | test("^###? Review:"; "i"))'
```

#### C. Code Factory AI review comments
Code Factory posts as `github-actions[bot]` with findings embedded in a single issue comment. Identify these by looking for the `**Claude finished` prefix or `### Code Review` heading:

```bash
gh api repos/{owner}/{repo}/issues/{pr}/comments --paginate | \
jq -r '.[] | select(.user.login == "github-actions[bot]" and (.body | test("### Code Review|Claude finished.*task in")))'
```

**Important**: Code Factory may post multiple review comments (one per push). Use the **most recent** one — it contains a "Previous Review Findings" status table showing what's already resolved. Only address findings marked as unresolved or new findings from the latest review.

### 2. Parse Findings by Source

#### Line-specific and general comments
Each comment = one finding. Read the referenced file and code section.

#### Code Factory comments
A single comment contains multiple findings in this structure:
```markdown
### P1 — Critical
#### <Finding title>
**`file.py:line`**
<description>
```code
<code snippet>
```
[Fix this →](link)

### P2 — High
#### <Finding title>
...
```

Extract each finding by:
1. Splitting on `#### ` headings under P1/P2/P3 sections
2. Parsing `**\`file.py:line\`**` for file and line references
3. Reading the description and suggestion text
4. **Ignoring** the "What looks good" section (no action needed)
5. **Ignoring** any findings already marked resolved in a "Previous Review Findings" table (rows with checkmarks/Fixed/Resolved)

### 3. Analyze Each Finding
For each finding (regardless of source):
- Reads the relevant file and code section
- Critically evaluates if suggestion is:
  - **Valid**: Issue is real, should be fixed
  - **Invalid**: False positive, not applicable
  - **Partial**: Issue valid but fix needs adjustment

### 4. Fix Valid Issues
- For valid findings: implements fix following existing patterns
- For partial: implements appropriate fix addressing the concern
- Documents why invalid findings are skipped

### 5. Reply

#### Line-specific comments
Reply inline: `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body="..."`

#### General PR-level comments
Summary comment: `gh api repos/{owner}/{repo}/issues/{pr}/comments`

#### Code Factory comments
Post a **single summary reply** as a new issue comment (there's no per-finding comment to reply to):

```markdown
## Addressed Code Factory Review

Responding to review from [comment](link_to_comment):

| # | Severity | File:Line | Finding | Action |
|---|----------|-----------|---------|--------|
| 1 | P1 | auth.py:42 | Missing auth guard | Fixed |
| 2 | P2 | utils.py:50 | Unbounded memory | Fixed |
| 3 | P3 | types.py:10 | Any type annotation | Skipped - not in changed code |
```

Replies are brief:
- Valid: "Fixed" or "Fixed - [note if approach differs]"
- Invalid: "Skipped - [brief reason]"
- Partial: "Addressed - [note on approach]"

### 6. Commit and Push
Commits all fixes with descriptive message and pushes.

## Evaluation Criteria

- **Security findings (P1)**: Take seriously, always verify the vulnerability is real
- **Unused imports**: Usually valid - remove them
- **Duplicate function calls**: Usually valid - cache results
- **Performance suggestions**: Evaluate if impact is meaningful
- **Architecture violations**: Check against CLAUDE.md patterns before dismissing
- **Documentation updates**: Valid if docs outdated
- **Test mock updates**: Valid if mocks don't match implementation
- **Refactoring suggestions**: Evaluate against KISS/YAGNI
- **"Previous findings still unresolved"**: Code Factory re-flags findings across review rounds — prioritize these as they've been raised before

## Output

Summary table of all findings addressed:

| # | Source | File:Line | Issue | Action | Reply |
|---|--------|-----------|-------|--------|-------|
| 1 | Code Factory P1 | auth.py:42 | Missing auth | Fixed | Posted summary |
| 2 | Copilot | test.py:100 | Incorrect mock | Fixed | Replied inline |
| 3 | Code Factory P3 | utils.py:50 | Suggested refactor | Skipped | Not needed per YAGNI |
