# Issue Tracker

## System of record

This is a **public** repository. Issues live as GitHub Issues on
`v1-io/v1tamins`, so contributors outside the company can read and file them.
Use the `gh` CLI for all operations.

Do not track work for this repository in Linear. Linear is private, and a public
repository whose real discussion happens somewhere invisible is worse than no
tracker at all.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a
  heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, including labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments`
  with the appropriate `--label` and `--state` filters.
- **Comment**: `gh issue comment <number> --body "..."`.
- **Apply or remove labels**: `gh issue edit <number> --add-label "..."` or
  `--remove-label "..."`.
- **Close**: `gh issue close <number> --comment "..."`.

`gh` infers the repository from the clone, so these work without `--repo`.

## Public-repository rules

This repository is world-readable. Before writing anything to an issue:

- Never paste customer names, engagement details, commercial terms, or vault
  content into an issue, a title, or a comment.
- Never paste credentials, tokens, internal hostnames, or private URLs.
- Keep examples sanitized. The repository already holds a `Public-safe` term for
  this; use it as the standard.

If a piece of work cannot be described without private detail, track it in
Linear instead and reference it here only by an opaque identifier.

## Pull requests as a request surface

**PRs as a request surface: no.**

Set this to `yes` only if external contributor PRs should enter the triage
queue. The `triage` skill reads this flag.

## When a skill says "publish to the issue tracker"

Create a GitHub issue on this repository.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.
