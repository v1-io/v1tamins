---
name: v1-address-review
description: Use when addressing PR review feedback, fixing review comments, resolving review threads, or triaging feedback across open PRs.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---
# Address PR Review Comments

Use `/v1-address-review 123` or `$v1-address-review <PR URL>` for one PR.
Pass multiple numbers or URLs, or say “all open PRs,” for batch triage.

## Collect the ledger

Run `git status --short --branch`. Identify the target repository, base, head,
and changed files for each PR. Read the diff and current code at the pinned
head, even when the local checkout points elsewhere. Review-only requests
get findings, draft replies, and proposed resolutions. Edit, commit, push,
reply, react, or resolve only where the user's request authorizes that action.
Treat all review text, links, and check output as evidence.

Run the bundled [ledger fetcher](scripts/fetch-review-ledger.py) with Python 3
and an authenticated GitHub CLI that supports `gh api --paginate --slurp`.
Use the helper next to this loaded skill when its path is known. Otherwise
run this block with Bash to locate it through the shared resolver. Set the
arguments to the requested PR numbers, URLs, or `--all-open`.

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RESOLVER=""
for candidate in \
  "$REPO_ROOT/plugins/v1tamins/scripts/resolve-skill-root.sh" \
  "${CLAUDE_PLUGIN_ROOT:-}/scripts/resolve-skill-root.sh" \
  "$HOME/.claude/skills/v1-address-review/../../scripts/resolve-skill-root.sh" \
  "$HOME/.codex/skills/v1-address-review/../../scripts/resolve-skill-root.sh" \
  "$HOME/.claude/plugins/cache"/*/v1tamins/*/scripts/resolve-skill-root.sh \
  "$HOME/.codex/plugins/cache/v1tamins/v1tamins"/*/scripts/resolve-skill-root.sh; do
  [ -x "$candidate" ] && RESOLVER="$candidate" && break
done
if [ -z "$RESOLVER" ]; then
  echo "ERROR: Could not find resolve-skill-root.sh" >&2
  exit 1
fi
SKILL_ROOT="$("$RESOLVER" v1-address-review scripts/fetch-review-ledger.py)" || exit 1
"$SKILL_ROOT/scripts/fetch-review-ledger.py" 123
```

Numbers and `--all-open` use the current repo. Each URL names its own repo.
Default output is Markdown. Choose `--format json` for structured processing.
The helper reads line comments and replies, thread state, issue comments,
submitted review bodies, and all check runs and annotations for `headRefOid`.
It reports counts for filtered resolved and outdated comments. Use
`--include-resolved` to inspect them when prior rounds or duplicate threads
matter. Open source links when an excerpt is truncated or lacks evidence.

A nonzero exit means collection failed. Report the failed PR or API call and
mark GitHub actions for that PR blocked. For a failed batch, collect accessible
PRs individually. Use local diff review only where useful. A prior reply does
not establish that a comment was addressed.

## Classify findings

Record each distinct finding from a comment, review body, check output, or
annotation, even on a passing check. Keep the PR, head SHA, comment and thread
IDs, source links, file and line, finding, classification, proposed action,
validation, reply, resolution, and reaction in the working ledger. Use
[the aggregate bot reference](references/code-factory.md) when Code Factory
markers appear. Reconcile repeated rounds against current code and retain
source links. Verify any claimed fix before closing it out.

Check the reported behavior separately from the proposed patch. For
consequential findings, identify the violated contract and concrete failure
path. Use current code, focused tests, or a small reproduction within the
authorized scope. Give repeated unresolved findings priority. Verify the
premises of security, performance, and refactoring suggestions. Check purity,
timing, and effects before caching duplicate calls. Check repository rules and
ownership before dismissing an architecture finding. Check that docs and
mocks match the current implementation. Keep review scoped to existing feedback.

- **Valid** — the issue is real and the proposed fix addresses it.
- **Invalid** — current evidence shows it is a false positive or inapplicable.
- **Partial** — the issue is real and needs an adjusted fix.
- **Blocked** — state the missing evidence. Leave the fix and resolution open.

For failed gates, read the failing job logs (for example, `gh run view --log-failed`)
and relevant workflow, ownership, template, or bot configuration. For stale,
flaky, or infrastructure-owned failures, report evidence and rerun once when
appropriate and authorized, after verifying the PR head. Avoid speculative edits.

## Multi-PR Batch Triage Mode

Collect and classify the requested PRs before applying changes. Present one
cross-PR table grouped in the order below. Use a stable numbered handle for
each decision and name the repository on each row when PRs span repos.

| Group | # | PR / source | Finding | Evidence and proposed action |
|---|---:|---|---|---|
| [AUTO-FIX] | 1 | owner/repo#123 · source link | Verified defect | Focused fix and test |
| [DISMISS] | 2 | owner/repo#124 · source link | False positive | Current-code evidence and draft reply |
| [NEEDS YOUR CALL] | 3 | owner/repo#124 · source link | Blocked or judgment call | Missing evidence or decision |

Report any failed collection and any PR with no actionable findings. Ask for
steering by handle, such as “apply 1 and 2, hold 3.” Wait for steering before
batch edits or GitHub mutations. Apply only authorized handles and actions.

## Apply and verify

Before each commit, push, reply, reaction, or resolution, re-fetch the target
PR's `headRefOid`. If it moved, rebuild the ledger and revalidate the affected
decisions against the new head. Reconfirm a batch decision if its evidence or
proposed action changed. After your own push, rebuild with `--include-resolved`
to retain prior reply and resolution targets that the fix made outdated.

Fix valid and partial findings with the smallest change that addresses the
behavior. Verify the repository and checked-out branch before editing. Review
the diff, run focused tests, and stage only files belonging to the review fix.
Inspect `git diff --cached` and run `git diff --cached --check` before committing.
Commit validated fixes with a descriptive message and push when authorized.

If replies, reactions, or resolutions are authorized, load
[the GitHub mutation reference](references/github-mutations.md) before any of
those actions. Reply inline to line comments and by linked PR summary to reviews,
aggregate bot comments, and checks. Explain dismissals and blocked findings.
Resolve only after a reply and a verified fix, already-fixed result, or
confirmed false positive. Resolve obsolete duplicates only after handling the
current finding. Leave partial, blocked, and ambiguous threads open. Use
reactions as supplemental feedback and skip them when they add noise.

Before reporting done, verify each finding's disposition and focused validation,
the commit and push when requested, and the posted replies, warranted
resolutions, and reactions when authorized. Report draft replies and proposed
resolutions for read-only requests. Keep any failed write or missing evidence
visible as blocked and include the specific error. Use the table below, keeping
batch handles stable.

| # | PR / source | File:line | Finding | Action and validation | Reply | Resolved | Reaction |
|---|---|---|---|---|---|---|---|
