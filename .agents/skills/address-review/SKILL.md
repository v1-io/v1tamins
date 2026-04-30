---
name: address-review
description: Use when addressing PR review comments or resolving unresolved PR review threads from Copilot, Code Factory, bots, or humans. Triggers on "fix review comments", "address review feedback", "address code factory", "respond to PR comments", "resolve conversations", "unresolved review threads".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# Address PR Review Comments

Fetch code review comments on a PR (from Copilot, Code Factory, bots, or humans), critically evaluate each one, fix the valid issues, reply to each comment, resolve conversations when warranted, and use usefulness reactions when appropriate.

## Usage

Typical invocations:
- Claude Code: `/address-review <PR_URL_or_NUMBER>`
- Codex: invoke `address-review` from the skills menu or use `$address-review <PR_URL_or_NUMBER>`

Examples:
```bash
/address-review https://github.com/your-org/your-repo/pull/123
/address-review 123
```

In Codex, the slash examples above map directly to `$address-review ...`.

## What It Does

### 0. Repository and Gate Preflight

- Run `git status --short --branch`.
- Identify the current branch, base branch, PR head SHA, and changed files.
- Leave unrelated local changes unstaged unless the user clearly wants them included.
- If review feedback is tied to a failed check or gate, inspect the failing check details before editing. Prefer `gh run view --log-failed` or the failing job logs when available.
- Inspect relevant `.github/` files when they explain the review surface: `CODEOWNERS`, pull request templates, workflow files for failed checks, and bot/gate configuration referenced by the PR or check output.
- If a failure is stale, flaky, or infrastructure-owned, report the evidence and rerun once when appropriate instead of making speculative code changes.

### 1. Build a Review Ledger

Before editing files, build a working ledger of every actionable review item:

| Comment ID | Thread ID | Source | File:Line | Finding | Status | Action | Validation | Reply | Resolve | Reaction |
|---|---|---|---|---|---|---|---|---|---|---|
| `<id>` | `<thread-id>` | Copilot / Code Factory / human | `path:line` | short title | valid / invalid / partial / blocked | fix / skip / ask | command or reason | posted / pending | yes / no / blocked | +1 / -1 / none |

Use the ledger to avoid losing line-specific comments, stale bot findings, or false positives that still need a reply. If GitHub API access fails, say so explicitly and do not claim comments were addressed; fall back only to local diff review and mark replies as blocked.

### 2. Fetch Review Comments
Checks **four** sources of review feedback:

#### A. Line-specific review comments
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate | \
jq -r '[.[] | select(.in_reply_to_id == null)] as $originals |
       [.[] | select(.in_reply_to_id != null)] as $replies |
       $originals | map(. as $original | $original + {
         replies: ($replies | map(select(.in_reply_to_id == $original.id)))
       })'
```

Do not drop an original comment only because it already has a reply. A replied comment may still need current-code verification, a follow-up reply, a reaction, or review-thread resolution.

#### B. PR-level issue comments (Copilot, humans, bots)
Fetch all PR-level issue comments, then classify them during analysis. Do not pre-filter to only comments with a `Review:` heading because human comments and some bot comments may still need a reply.

```bash
gh api repos/{owner}/{repo}/issues/{pr}/comments --paginate
```

#### C. Code Factory AI review comments
Code Factory posts as `github-actions[bot]` with findings embedded in a single issue comment or summarized in the current Code Factory status comment. Identify these by looking for the `**Claude finished` prefix, `### Code Review` heading, `## Code Factory` heading, or `code-factory-rerun` marker:

```bash
gh api repos/{owner}/{repo}/issues/{pr}/comments --paginate | \
jq -r '.[] | select(.user.login == "github-actions[bot]" and (.body | test("### Code Review|## Code Factory|Claude finished.*task in|code-factory-rerun")))'
```

**Important**: Code Factory may post multiple review comments (one per push). Use the **most recent** one — it may contain a "Previous Review Findings" status table showing what's already resolved, or it may be a summary-only status comment whose actionable findings are in line-specific review comments. Only address findings marked as unresolved or new findings from the latest review.

#### D. Review threads and conversation state
Fetch review threads so comments can be resolved after they are answered:

```bash
gh api graphql \
  -f owner='{owner}' \
  -f repo='{repo}' \
  -F number={pr} \
  -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 50) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              databaseId
              author { login }
              body
              path
              line
              originalLine
              url
            }
          }
        }
      }
    }
  }
}'
```

If `reviewThreads.pageInfo.hasNextPage` is true, continue fetching with `after: <endCursor>` until all thread pages are loaded. If any thread's `comments.pageInfo.hasNextPage` is true, fetch additional comment pages for that thread before deciding whether it has been answered or can be resolved.

Join review threads to line-specific comments by GraphQL `databaseId` matching the REST comment `id`. Track unresolved and outdated thread state in the ledger.

Record the PR head SHA before analysis:

```bash
gh pr view {pr} --repo {owner}/{repo} --json headRefOid --jq .headRefOid
```

Before posting replies, adding reactions, resolving threads, committing, or pushing, fetch the head SHA again. If it changed, rebuild the ledger against the new head first.

### 3. Parse Findings by Source

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

If the latest Code Factory comment is summary-only, use it as gate/status context and rely on current line-specific review comments for the actionable finding ledger.

### 4. Analyze Each Finding
For each finding (regardless of source):
- Reads the relevant file and code section
- Critically evaluates if suggestion is:
  - **Valid**: Issue is real, should be fixed
  - **Invalid**: False positive, not applicable
  - **Partial**: Issue valid but fix needs adjustment

### 5. Fix Valid Issues
- For valid findings: implements fix following existing patterns
- For partial: implements appropriate fix addressing the concern
- Documents why invalid findings are skipped
- Review `git diff` and, when relevant, `git diff --staged` before committing.
- Stages only files changed for the review fix, especially in noisy worktrees.
- Run the fastest relevant validation inferred from the touched files.
- Run `git diff --cached --check` or an equivalent staged-file check before committing when unrelated local files may already have whitespace or generated-output churn.

### 6. Reply

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
- Blocked: "Could not verify/reply because [specific GitHub/API/tooling failure]"

### 7. Resolve Conversations and React

After replying, resolve each review thread only when doing so is justified:

- Resolve a thread when the finding was fixed, was already fixed in current code, or was a confirmed false positive with a clear reply.
- Resolve older duplicate or outdated threads only after the equivalent current finding is fixed or clearly dismissed.
- Do not resolve a thread when work is partial, blocked, needs the reviewer to answer a question, or the current code still leaves reasonable ambiguity.
- Do not resolve aggregate issue comments, because GitHub only resolves review threads.
- If thread resolution fails, keep the ledger row `blocked` and include the exact API/tooling failure in the final output.

Resolve a thread with GraphQL:

```bash
gh api graphql \
  -f threadId='{thread-id}' \
  -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}'
```

Use reactions when they add signal:

- Add `+1` to useful, valid, actionable review comments after fixing or accepting the finding.
- Add `-1` only for bot comments that are materially false, misleading, or unactionable after current-code verification. Prefer a written explanation over a `-1` for good-faith human feedback.
- Skip reactions when the comment is mixed, ambiguous, purely conversational, or already has the same reaction from the current actor.
- Do not use reactions as a substitute for replies. A reaction supplements the written disposition.

Before adding a reaction, fetch existing reactions and the current GitHub actor:

```bash
gh api user --jq .login
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions \
  -H "Accept: application/vnd.github+json"
gh api repos/{owner}/{repo}/issues/comments/{comment_id}/reactions \
  -H "Accept: application/vnd.github+json"
```

React to line-specific review comments:

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions \
  -H "Accept: application/vnd.github+json" \
  -f content='+1'
```

React to PR-level issue comments:

```bash
gh api repos/{owner}/{repo}/issues/comments/{comment_id}/reactions \
  -H "Accept: application/vnd.github+json" \
  -f content='-1'
```

### 8. Commit and Push
Commit all validated fixes with a descriptive message and push when the user asked to complete the review-fix loop. Do not leave the PR in a state where local fixes exist but review comments are unanswered.

## Evaluation Criteria

- **Security findings (P1)**: Take seriously, always verify the vulnerability is real
- **Unused imports**: Usually valid - remove them
- **Duplicate function calls**: Usually valid - cache results
- **Performance suggestions**: Evaluate if impact is meaningful
- **Architecture violations**: Check `AGENTS.md`, `CLAUDE.md`, relevant `.github/` ownership/workflow guidance, and equivalent repo guidance before dismissing
- **Documentation updates**: Valid if docs outdated
- **Test mock updates**: Valid if mocks don't match implementation
- **Refactoring suggestions**: Evaluate against KISS/YAGNI
- **"Previous findings still unresolved"**: Code Factory re-flags findings across review rounds — prioritize these as they've been raised before

## Completion Gates

Before reporting done:

- Every valid or partial finding has a code change or a clear reason it is blocked.
- Every invalid finding has a concise explanation grounded in current file contents.
- Focused tests or validation commands have run for the changed surface.
- Only review-fix files are staged.
- The commit is pushed if the user asked for push/PR completion.
- Every GitHub review thread or aggregate bot comment has a reply, unless API access was unavailable and that gap is stated.
- Every review thread that should be resolved is resolved, unless GitHub API access was unavailable and that gap is stated.
- Usefulness reactions are applied for clearly useful or clearly unhelpful bot/human comments when appropriate, and skipped when they would add noise.

## Output

Summary table of all findings addressed:

| # | Source | File:Line | Issue | Action | Reply | Resolved | Reaction |
|---|--------|-----------|-------|--------|-------|----------|----------|
| 1 | Code Factory P1 | auth.py:42 | Missing auth | Fixed | Posted summary | n/a | +1 |
| 2 | Copilot | test.py:100 | Incorrect mock | Fixed | Replied inline | Yes | +1 |
| 3 | Code Factory P3 | utils.py:50 | Suggested refactor | Skipped | Not needed per YAGNI | Yes | -1 |
