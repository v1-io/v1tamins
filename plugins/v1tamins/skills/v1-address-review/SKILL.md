---
name: v1-address-review
description: Use when resolving existing PR review comments or threads. Triggers on "address review feedback", "fix review comments", or "resolve review threads".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Address PR Review Comments

Fetch code review comments on a PR (from humans, Copilot, or aggregate bot reviews), critically evaluate each one, fix the valid issues, reply to each comment, resolve conversations when warranted, and use usefulness reactions when appropriate.

## Usage

Typical invocations:
- Claude Code: `/v1-address-review <PR_URL_or_NUMBER>`
- Codex: invoke `v1-address-review` from the skills menu or use `$v1-address-review <PR_URL_or_NUMBER>`

Examples:
```bash
/v1-address-review https://github.com/your-org/your-repo/pull/123
/v1-address-review 123
```

In Codex, the slash examples above map directly to `$v1-address-review ...`.

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
| `<id>` | `<thread-id>` | Copilot / bot / human | `path:line` | short title | valid / invalid / partial / blocked | fix / skip / ask | command or reason | posted / pending | yes / no / blocked | +1 / -1 / none |

Use the ledger to avoid losing line-specific comments, stale bot findings, or false positives that still need a reply. If GitHub API access fails, say so explicitly and do not claim comments were addressed; fall back only to local diff review and mark replies as blocked.

### 2. Fetch Review Comments
Check every source of review feedback:

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

#### C. Aggregate bot review comments
When a bot packs multiple findings into one issue comment (Code Factory is the reference dialect), load [references/code-factory.md](references/code-factory.md) for detect/parse/summary-reply rules. Keep using the generic ledger; do not special-case other bots unless their body matches those multi-finding markers.

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

#### E. Submitted review bodies

Fetch submitted reviews because an approval, comment, or request-changes review can contain actionable feedback only in its top-level body:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/reviews --paginate
```

Treat every non-empty review body as a review item. Join it to its review author, state, commit ID, and URL in the ledger. Do not assume its line comments duplicate the body.

#### F. Check-run output and annotations

Fetch every check run for the recorded PR head SHA, then fetch every annotation for every run:

```bash
gh api repos/{owner}/{repo}/commits/{head-sha}/check-runs --paginate
gh api repos/{owner}/{repo}/check-runs/{check-run-id}/annotations --paginate
```

Inspect each check run's status, conclusion, details URL, and `output.title`, `output.summary`, and `output.text`, as well as every annotation's level, path, lines, title, message, and raw details. Record actionable output or annotations in the ledger even when the overall check passes. Do not treat a successful conclusion as proof that a check supplied no feedback.

Record the PR head SHA before analysis:

```bash
gh pr view {pr} --repo {owner}/{repo} --json headRefOid --jq .headRefOid
```

Before posting replies, adding reactions, resolving threads, committing, or pushing, fetch the head SHA again. If it changed, rebuild the ledger against the new head first. If the user did not explicitly ask to respond to or resolve PR feedback, draft the replies and proposed resolutions instead of mutating GitHub.

### 3. Parse Findings by Source

#### Line-specific and general comments
Each comment = one finding. Read the referenced file and code section.

#### Submitted reviews and check feedback
Treat each distinct finding in a submitted review body, check output, or check annotation as a ledger item. Use its review URL or check details URL as the source when no line-comment URL exists.

#### Aggregate bot comments
Follow [references/code-factory.md](references/code-factory.md) when the body matches multi-finding markers. Otherwise treat the issue comment as a single finding like any other PR-level comment.

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

#### Submitted reviews and check feedback
Post one PR-level summary comment that links each source review or check and records the disposition of every finding that cannot receive an inline reply.

#### Aggregate bot multi-finding comments
Use the summary-reply template in [references/code-factory.md](references/code-factory.md).

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
- **Repeated unresolved findings across bot rounds**: Prioritize — see [references/code-factory.md](references/code-factory.md)

## Completion Gates

Before reporting done:

- Every valid or partial finding has a code change or a clear reason it is blocked.
- Every invalid finding has a concise explanation grounded in current file contents.
- Focused tests or validation commands have run for the changed surface.
- Only review-fix files are staged.
- The commit is pushed if the user asked for push/PR completion.
- Every GitHub review thread or aggregate bot comment has a reply, unless API access was unavailable and that gap is stated.
- Every submitted review-body finding and check-run finding has a disposition and a linked PR-level reply when no inline reply surface exists.
- Every review thread that should be resolved is resolved, unless GitHub API access was unavailable and that gap is stated.
- Usefulness reactions are applied for clearly useful or clearly unhelpful bot/human comments when appropriate, and skipped when they would add noise.

## Output

Summary table of all findings addressed:

| # | Source | File:Line | Issue | Action | Reply | Resolved | Reaction |
|---|--------|-----------|-------|--------|-------|----------|----------|
| 1 | Aggregate bot P1 | auth.py:42 | Missing auth | Fixed | Posted summary | n/a | +1 |
| 2 | Copilot | test.py:100 | Incorrect mock | Fixed | Replied inline | Yes | +1 |
| 3 | Aggregate bot P3 | utils.py:50 | Suggested refactor | Skipped | Not needed per YAGNI | Yes | -1 |
