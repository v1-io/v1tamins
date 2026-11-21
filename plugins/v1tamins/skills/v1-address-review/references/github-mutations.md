# GitHub replies, resolutions, and reactions

Load this reference when authorized to post a reply, resolve a review thread,
or add a reaction. Use IDs and repository identity from the ledger. Immediately
before each write, compare the current PR head with the ledger's `headRefOid`.
For multiple PRs, also check that the selected handle and action were approved.

In the examples, set `PR_URL` to the exact PR URL. Set `HOST` and `REPO` from
that URL, `PR` to its number, and `COMMENT_ID` or `THREAD_ID` to the target ID.
Set `BODY` to the complete reply as data. Use the same host for all API calls.

```bash
gh pr view "$PR_URL" --json headRefOid --jq .headRefOid
```

If the SHA differs or cannot be read, stop writes for that PR. Rebuild the
ledger after a head change and revalidate the dispositions. Record any GitHub
failure as blocked and keep the exact error for the handoff.

## Reply

Use a brief disposition. Say “Fixed” with a note when the approach differs,
“Skipped” with a current-code reason, “Addressed” with the adjusted approach,
or “Could not verify” with the missing evidence or specific failure. Verify
the returned comment URL and record it in the ledger.

Reply to the original comment in a line-specific thread.

```bash
gh api --hostname "$HOST" --method POST \
  "repos/$REPO/pulls/$PR/comments/$COMMENT_ID/replies" \
  --raw-field "body=$BODY" --jq .html_url
```

Use a PR-level comment for issue comments, submitted reviews, checks, and
aggregate findings that lack inline reply endpoints. Post one linked summary
covering those findings on the PR. Link each addressed review, check, or
comment, including repeated aggregate rounds, and record each disposition.

```bash
gh api --hostname "$HOST" --method POST "repos/$REPO/issues/$PR/comments" \
  --raw-field "body=$BODY" --jq .html_url
```

## Resolve a review thread

After a clear reply, resolve a thread when the finding was fixed, already
fixed at the current head, or confirmed to be a false positive. Resolve older
duplicate or outdated threads after the equivalent current finding has been
fixed or dismissed. Leave partial, blocked, and ambiguous threads open,
including threads waiting for the reviewer. GitHub resolution applies only to
review threads. Confirm that the response contains the expected thread ID and
`isResolved: true`.

```bash
gh api graphql --hostname "$HOST" --raw-field "threadId=$THREAD_ID" \
  --raw-field 'query=
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}'
```

## React

Use `+1` for useful, valid, actionable comments after fixing or accepting the
finding. Reserve `-1` for verified bot comments that are materially false,
misleading, or unactionable. For good-faith human feedback, use a written
explanation. Skip mixed, ambiguous, and conversational comments. A reaction
supplements the written disposition.

Before adding a reaction, fetch the current actor and all existing reactions.
Choose the endpoint for the comment type. Skip the write if the actor already
added that reaction. Recheck the PR head before writing.

```bash
gh api --hostname "$HOST" user --jq .login
# For a line-specific review comment:
REACTIONS="repos/$REPO/pulls/comments/$COMMENT_ID/reactions"
# For an issue comment, use repos/$REPO/issues/comments/$COMMENT_ID/reactions.
gh api --hostname "$HOST" "$REACTIONS" --paginate --slurp \
  -H "Accept: application/vnd.github+json"
gh api --hostname "$HOST" --method POST "$REACTIONS" \
  -H "Accept: application/vnd.github+json" --raw-field "content=$REACTION"
```

Check the returned actor and content. Keep skipped and failed reactions visible
in the ledger. React to an aggregate issue comment only when the comment as a
whole warrants it.
