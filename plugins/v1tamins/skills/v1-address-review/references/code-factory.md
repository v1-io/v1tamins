# Aggregate bot review adapter (Code Factory example)

Use this reference when an issue comment packs several findings into one body.
The ledger fetcher recognizes `**Claude finished`, `### Code Review`,
`## Code Factory`, and `code-factory-rerun` markers. It extracts `####` findings
under `### P1`, `### P2`, and `### P3` sections, with file and line when the
finding contains a bold code span such as **`src/file.py:42`**. It skips the
“What looks good” section and keeps summary text as status context. When the
dialect differs, open the source and classify any additional findings manually.

Use each round as evidence. A summary-only comment may contain gate status or
a “Previous Review Findings” table. An omitted finding stays in the ledger
until it has a verified disposition. Check Fixed and Resolved claims against
the pinned head. Prioritize items re-flagged as unresolved. Reconcile repeated
findings by current behavior, keeping links to every round.

For authorized replies, include one row per disposition in the linked PR
summary. Mention the source aggregate comment or comments above the table.

| # | Severity | File:line | Finding | Action |
|---|---|---|---|---|
| 1 | P1 | auth.py:42 | Missing authentication guard | Fixed |
| 2 | P2 | cache.py:50 | Unbounded memory | Fixed |
| 3 | P3 | types.py:10 | Suggested annotation | Skipped. The type is inferred. |
