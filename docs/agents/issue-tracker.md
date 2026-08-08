# Issue Tracker

## System of record

This repository is company work. Issues live in Linear.

- Workspace: `v1io` (organization name "Humm")
- Team: `VER` (PDE) for product and engineering work
- Team: `GTM` for go-to-market work

Issue URLs take the form `https://linear.app/v1io/issue/VER-123`. Always render
a task ID as a clickable link in that form. Never fabricate an issue ID or link.

GitHub hosts the source and pull requests. GitHub Issues is not the
work-tracking system for this repository.

## Access

Use the Linear API directly, not an MCP server. Read `LINEAR_API_KEY` from the
environment and never print its value. The `linear-api` skill carries the
working queries and scripts; start there rather than hand-writing GraphQL.

## Task contract

- Put the outcome in the issue title. Put context, constraints, and acceptance
  evidence in the description.
- Move an issue's state in Linear rather than describing its status in this
  repository. Linear is the source of truth for state.
- Reference the issue ID in branch names, commit trailers, and PR bodies so the
  cross-link survives outside Linear.

Do not duplicate live issue status in this repository.

## When a skill says "publish to the issue tracker"

Create a Linear issue on team `VER` unless the work is clearly go-to-market, in
which case use `GTM`.

## When a skill says "fetch the relevant ticket"

Read the Linear issue by its identifier, including comments.

## Pull requests as a request surface

**PRs as a request surface: no.**
