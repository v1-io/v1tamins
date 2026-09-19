---
name: v1-changelog
description: Use when writing release notes from merged PRs. Triggers on "write changelog", "release notes", or "what shipped".
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---
# Write Changelog

Write release notes from PRs merged since the last changelog. This writes new
release notes; to sync existing docs (README, AGENTS.md, guides) with what
shipped, use `v1-docs-freshness`.

## Usage

Typical invocations:
- Claude Code: `/v1-changelog`
- Codex: invoke `v1-changelog` from the skills menu or use `$v1-changelog`

## Workflow

1. **Find the latest changelog**
   - Check the changelog directory (e.g., `docs/internal/changelog/` or `$CHANGELOG_DIR`)
   - Identify the most recent file by the date in its name

2. **Fetch recent PRs**
   - Use the GitHub API to get PRs merged to main since that changelog
   - Pull titles, descriptions, and metadata

3. **Write the new changelog**
   - Create a markdown file with the date in the filename
   - Follow the project's conventions

## Changelog Format

The changelog follows this structure:

- **1-3 Most Impactful Changes** (heading 2 each)
  - Title: 1-3 words describing the change
  - Description: 1-2 sentences explaining the change
  - Placeholder for visual (screenshot/diagram)

- **Summary of Smaller Changes** (if applicable)
  - High-level bullets for minor updates

## Focus

- User-facing changes and new features
- Breaking changes, put them first
- Major bug fixes and improvements
- Skip internal refactors unless they matter to users

## Example Structure

```markdown
# Changelog - 2026-01-07

## Saved filters

You can save a filter and come back to it. Combine conditions with AND/OR, and
apply them across related tables.

[Placeholder for screenshot]

## Faster large exports

CSV export no longer times out on big tables.

[Placeholder for screenshot]

## Additional Updates

- Safari no longer drops you after the login timeout
- Failed data-source connections now say what actually broke
- Form labels meet contrast requirements
```

## Notes

- Requires GitHub CLI (`gh`) to be installed and authenticated
- Changelog saved to your changelog directory (e.g., `docs/internal/changelog/YYYY-MM-DD.md`)
- Write for users, not the implementation
