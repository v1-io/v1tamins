---
name: v1-pr-description
description: Use when writing or updating a GitHub PR title or description. Triggers on "write PR description", "update PR body", or "PR title".
allowed-tools:
  - Bash
  - Read
  - Grep
---
# Generate PR Description

Write or update the PR title and description from the actual diff, current PR
metadata, repo guidance, and the user's constraints.

## Usage

Typical invocations:
- Claude Code: `/v1-pr-description <PR_URL_or_NUMBER>`
- Codex: invoke `v1-pr-description` from the skills menu or use `$v1-pr-description <PR_URL_or_NUMBER>`

Examples:
```bash
/v1-pr-description https://github.com/your-org/your-repo/pull/123
/v1-pr-description 123
```

In Codex, the slash examples above map directly to `$v1-pr-description ...`.

## Workflow

### 1. Resolve PR Context

Use the PR itself as the source of truth for base/head instead of assuming `main`:

```bash
gh pr view {pr} --json number,url,title,body,baseRefName,baseRefOid,headRefName,headRefOid,headRepository,headRepositoryOwner,files,commits
```

Treat the repository named by the PR URL as the base repository. Confirm its
primary GitHub identity before using local refs:

```bash
gh repo view {host}/{owner}/{repo} --json nameWithOwner
```

The base identity, the current base branch ref from the Git ref API, and local
`HEAD` are one contract. The PR metadata `baseRefOid` is historical context;
an open PR can retain it after the base branch advances. The local checkout is
usable only when `HEAD` equals `headRefOid`, a local remote URL maps to the
GitHub base repository, the authoritative API response is a commit for the
requested `refs/heads/{baseRefName}`, and a successful fetch resolves to that
same current SHA. Re-read the repository identity after resolving the ref so a
concurrent repository change fails closed. Do not choose a remote because it
is named `origin` or `upstream`, and do not use an existing remote-tracking ref
after a failed fetch. If any check fails, stop with an explicit unavailable
diff context and do not draft or update the description from that local diff.

Optional helper:

Run this shell block with Bash. If your tool defaults to zsh or another shell,
select Bash first; cache glob handling depends on it.

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RESOLVER=""
for candidate in \
  "$REPO_ROOT/plugins/v1tamins/scripts/resolve-skill-root.sh" \
  "${CLAUDE_PLUGIN_ROOT:-}/scripts/resolve-skill-root.sh" \
  "$HOME/.claude/skills/v1-pr-description/../../scripts/resolve-skill-root.sh" \
  "$HOME/.codex/skills/v1-pr-description/../../scripts/resolve-skill-root.sh" \
  "$HOME/.claude/plugins/cache"/*/v1tamins/*/scripts/resolve-skill-root.sh \
  "$HOME/.codex/plugins/cache/v1tamins/v1tamins"/*/scripts/resolve-skill-root.sh; do
  [ -x "$candidate" ] && RESOLVER="$candidate" && break
done
if [ -z "${RESOLVER:-}" ]; then
  echo "ERROR: Could not find resolve-skill-root.sh" >&2
  exit 1
fi
SKILL_ROOT="$("$RESOLVER" v1-pr-description generate.sh)"

"$SKILL_ROOT/generate.sh" {PR_URL_or_NUMBER}
```

Use the helper to collect metadata, changed files, commits, and verified diff
context. Treat its output as evidence, not as the finished PR description. A
successful helper run (exit `0`) is required before using its local diff; exit
`2` means the metadata was collected but the diff context is unavailable.

If you need to inspect the context manually, fetch the mapped base remote and
resolve the current branch revision from the primary Git ref API, then prove
the exact revision before diffing:

```bash
base_sha="$(gh api --hostname {host} repos/{owner}/{repo}/git/ref/heads/{baseRefName} \
  --jq 'select(.ref == "refs/heads/{baseRefName}" and .object.type == "commit") | .object.sha')"
test -n "$base_sha"
git fetch <base-remote> refs/heads/{baseRefName}
test "$(git rev-parse FETCH_HEAD^{commit})" = "$base_sha"
git diff --stat "$base_sha"...HEAD
git diff --name-only "$base_sha"...HEAD
git log --oneline "$base_sha"..HEAD
```

If the current checkout does not match the PR head SHA, or the base identity or
exact base revision cannot be proved, say so and stop the local-diff workflow.
Do not write a description from an unknown local branch or stale base ref.

### 2. Build a Ledger

Before drafting, build a compact ledger:

| Source | Evidence | Use |
|---|---|---|
| PR metadata | title, body, base/head, files | preserve existing context and detect stale claims |
| Diff | changed files and meaningful hunks | describe actual behavior changes |
| Commits | commit subjects and range | identify intent and follow-up fixes |
| Validation | test commands in commits, comments, checks, or user notes | report only verified validation |
| Repo guidance | `AGENTS.md`, `CLAUDE.md`, `.github/pull_request_template*`, `.github/CODEOWNERS`, relevant workflows | match local expectations |
| User constraints | required phrases, prohibited terms, title/body preferences | preserve exactly |

Read only the relevant files. Do not crawl all of `.github/`; inspect files that explain PR templates, ownership, or checks touched by the PR.

If the existing PR body has required footer text, checklist state, reviewer notes, linked tickets, or user-requested wording, preserve it unless the user explicitly asks to replace it.

### 3. Draft Title and Body

Title:
- Keep it concise and specific, usually under 72 characters.
- Preserve issue keys or required prefixes already present in the title.
- Use imperative or conventional style only if the repository already uses it.

Body:
- Prefer this structure, omitting sections that have no grounded content:

```markdown
## Summary
- ...

## Changes
- ...

## Validation
- ...

## Risk / Rollback
- ...

## Notes for Reviewers
- ...
```

Use bullets over prose when the PR has multiple concrete changes. Keep the description grounded in files, behavior, validation, and reviewer impact.

Choose the smallest representation that clarifies a consequential change:
a structural before/after for responsibilities, a call-tree for execution,
pseudocode for a branch, or Mermaid for relationships. Include it only when it
adds information beyond the prose and fits the repository template. Ground
it in the ledger; skip it when ordinary prose is sufficient. Use
`v1-pr-walkthrough` for a fuller explanation, not a larger artifact by default.

For an actual responsibility change, a small structural comparison may suffice:

```text
Before: command → parse + authorize + mutate + format
After:  command → validated request → scoped mutation → result formatter
```

Keep Mermaid diagrams small and maintainable. Do not add a diagram for a
simple list of changes.

```mermaid
flowchart LR
  "Old path" --> "Changed component"
  "Changed component" --> "New behavior"
```

If a relevant explainer video already exists, link it as supplementary explanation alongside the concise written summary. Verify which PR revision it covers and whether reviewers can access its destination; disclose material staleness and keep an inaccessible local file out of the posted body. Creating or uploading a video is not part of writing a PR description unless requested. A video explains the change; it does not replace validation evidence.

### 4. Check the Draft Before Posting

Before editing GitHub:
- Check that every major claim in the draft is backed by the ledger.
- Check that the title/body matches the current diff, not a stale earlier version of the PR.
- Verify validation claims are commands that actually ran, check results that passed, or explicitly marked as not run.
- Scan for prohibited terms or wording the user asked to avoid.
- Confirm required text from the old body is still present when it should be preserved.
- If the PR changed after the ledger was built, rebuild the ledger first.

If the implementation no longer matches the existing PR description, update the stale description rather than preserving inaccurate text.

### 5. Update GitHub

Use `gh pr edit` when the user asked to update GitHub:

```bash
gh pr edit {pr} --title "..." --body-file /path/to/body.md
```

If `gh` is unavailable or unauthenticated, do not claim the PR was updated. Return the proposed title/body and the exact blocker.

If the user only asked for a draft, return the proposed title/body without running `gh pr edit`.

## Output

Report:
- PR URL or number.
- Whether GitHub was updated or only a draft was produced.
- Title used.
- Key evidence sources consulted.
- Validation claims included.
- Any preserved required text or prohibited terms checked.
