---
name: v1-pr-description
description: Use when writing, updating, or auditing a GitHub PR title or description. Triggers on "write PR description", "update PR body", "describe this PR", "refresh PR description", "PR title".
allowed-tools:
  - Bash
  - Read
  - Grep
---
# Generate PR Description

Write or update a grounded pull request title and description from the actual PR diff, current PR metadata, repository guidance, and user constraints.

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
gh pr view {pr} --json number,url,title,body,baseRefName,headRefName,headRefOid,files,commits
```

Optional helper:

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

Use the helper to collect metadata, changed files, commits, and merge-base diff context. Treat its output as evidence, not as the finished PR description.

Fetch enough refs to compare against the actual base branch:

```bash
git fetch origin {baseRefName}
merge_base="$(git merge-base origin/{baseRefName} HEAD)"
git diff --stat "$merge_base"...HEAD
git diff --name-only "$merge_base"...HEAD
git log --oneline "$merge_base"..HEAD
```

If the current checkout does not match the PR head SHA, say so and either check out the PR branch or base the description on GitHub metadata plus fetched refs. Do not write a description from an unknown local branch.

### 2. Build a Grounding Ledger

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

Add a Mermaid diagram only when it materially clarifies a flow, architecture change, state transition, migration path, or review sequence. Keep diagrams small and maintainable. Do not add a diagram for a simple list of changes.

```mermaid
flowchart LR
  "Old path" --> "Changed component"
  "Changed component" --> "New behavior"
```

### 4. Validate Alignment Before Posting

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
