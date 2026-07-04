---
name: v1-docs-freshness
description: Use when existing documentation (README, AGENTS.md, CLAUDE.md, guides) should be synchronized after code changes or shipped work. Triggers on "update the docs", "sync docs", "post-ship docs", "documentation is stale", "refresh README". For generating release notes from merged PRs, use v1-changelog.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - AskUserQuestion
---
# Docs Freshness

Bring project documentation back in sync with the code that just changed.

## Workflow

### 1. Establish Scope

Determine the base branch and current change set:

```bash
git branch --show-current
git diff --stat
git diff --name-only
git log --oneline -10
```

If the user gave a PR, ticket, or release range, inspect that scope instead of assuming the current branch.

Classify the change:
- New user-facing capability
- Changed behavior
- Removed capability
- New skill, command, script, hook, or config surface
- Infrastructure, install, test, or contributor workflow change
- Docs-only change

### 2. Find Docs

Discover documentation files before editing:

```bash
rg --files -g "*.md" -g "!node_modules/**" -g "!.git/**" | sort
```

Always include entry-point docs when they exist: `README.md`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, and `docs/**/*.md`. Treat `CHANGELOG.md` as a read-only source here — *generating* release notes from merged PRs is `v1-changelog`'s job; this skill only keeps the other docs consistent with what shipped.

### 3. Audit Each Doc

Cross-check each relevant doc against the changed files.

Use this classification:
- **Auto-update:** factual corrections clearly required by the diff, such as tables, counts, command names, paths, install steps, or project tree entries.
- **Ask first:** positioning, removals, security descriptions, architecture rationale, large rewrites, or anything where the diff does not prove the right wording.
- **Leave alone:** docs that remain accurate or intentionally historical.

Do not ask about facts that are directly visible in the repo. Read first, then ask only for product judgment or narrative choices.

### 4. Apply Safe Updates

Make factual updates directly. Keep edits narrow and preserve the existing voice.

Examples:
- Add a new skill to the skills table.
- Update a command count after adding or removing command files.
- Fix install instructions when a script path changed.
- Add discoverability links for new docs.

Do not silently remove whole sections. Do not rewrite the README positioning unless the user explicitly asks.

### 5. Handle Changelogs Carefully

If `CHANGELOG.md` changed, treat it as source material, not scratch space.

Rules:
- Read the whole relevant entry first.
- Polish wording only inside existing entries.
- Never delete, reorder, or regenerate entries.
- If an entry appears factually wrong, ask before changing it.
- Use targeted edits. Never overwrite `CHANGELOG.md`.

### 6. Cross-Doc Pass

Before finishing, check for contradictions:
- README feature list vs. `CLAUDE.md` or `AGENTS.md`
- Architecture docs vs. actual folders and scripts
- Skill lists vs. `plugins/v1tamins/skills`
- Setup docs vs. the install path the project actually uses

Also check discoverability. Important docs should be reachable from `README.md`, `CLAUDE.md`, or a docs index.

### 7. TODO and Version Pass

If `TODOS.md` exists, compare open items against the diff. Mark items complete only when the branch clearly completed them.

If a `VERSION` file exists, never bump it without asking. Recommend "skip" for docs-only work unless the docs are part of a release.

### 8. Verify

Run cheap checks:

```bash
git diff --check
git diff --name-only
```

Report:
- Docs modified
- Important docs checked but left unchanged
- Questions or deferred decisions
- Any verification command that failed

Do not commit unless the user explicitly asked for a commit.
