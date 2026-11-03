# Issue Tracker

## System of record

Maintainers track accepted work for this repository in their private Linear
workspace. Every issue carries the `repo:v1tamins` label. Agents with Linear
access use the Linear route from their own environment instructions; this
public file does not name the workspace, team, or credentials.

GitHub Issues on `v1-io/v1tamins` stay open as a public intake. Anyone can
report a bug or request there. A maintainer triages each report into Linear or
closes it.

## Triage a GitHub issue

1. Read it: `gh issue view <number> --comments`.
2. Check the report against current `main` before keeping it.
3. Decide:
   - **Still real**: create a Linear issue with the `repo:v1tamins` label and
     the current evidence. Close the GitHub issue with a comment that gives
     the Linear identifier only, for example `VER-1234`, never a Linear URL.
   - **Already fixed**: close it as completed and name the pull request.
   - **Not wanted**: close it as not planned with a one-line reason.

`gh` infers the repository from the clone, so these commands work without
`--repo`.

## Public-repository rules

GitHub issues, titles, and comments are world-readable. Linear is private.

- Never paste customer names, engagement details, commercial terms, or vault
  content into a GitHub issue, title, or comment.
- Never paste credentials, tokens, internal hostnames, or private URLs,
  including Linear URLs.
- Keep examples sanitized. The repository already holds a `Public-safe` term for
  this; use it as the standard.

## Pull requests as a request surface

**PRs as a request surface: no.**

Set this to `yes` only if external contributor PRs should enter the triage
queue.

## When a skill says "publish to the issue tracker"

Create a Linear issue with the `repo:v1tamins` label. Without Linear access,
create a GitHub issue instead and leave it for maintainer triage.

## When a skill says "fetch the relevant ticket"

For a Linear identifier, read it through the Linear route. For a GitHub issue
number or URL, run `gh issue view <number> --comments`.
