# Aggregate bot review adapter (Code Factory example)

Use this adapter when a PR-level bot comment packs multiple findings into one body (Code Factory is the reference dialect). Keep the generic `v1-address-review` ledger and reply/resolve flow for line comments and ordinary issue comments.

## Detect

Posts often appear as `github-actions[bot]` with one or more of:
- `**Claude finished` prefix
- `### Code Review` heading
- `## Code Factory` heading
- `code-factory-rerun` marker

```bash
gh api repos/{owner}/{repo}/issues/{pr}/comments --paginate | \
jq -r '.[] | select(.body | test("### Code Review|## Code Factory|Claude finished.*task in|code-factory-rerun"))'
```

The bot may post multiple review comments (one per push). Inventory findings from
every matching round. Use the most recent comment as status context, including
any "Previous Review Findings" table or summary-only comment. Reconcile repeated
findings against the current PR head and deduplicate them in the generic ledger;
retain their source links. An older finding does not disappear merely because
the newest summary omits it. Treat Fixed/Resolved labels as claims to verify in
current code, then record the disposition rather than dropping the item.

## Parse multi-finding bodies

A single comment often contains multiple findings:

```markdown
### P1 — Critical
#### <Finding title>
**`file.py:line`**
<description>
```code
<code snippet>
```
[Fix this →](link)

### P2 — High
#### <Finding title>
...
```

Extract each finding by:
1. Splitting on `#### ` headings under P1/P2/P3 sections
2. Parsing `**\`file.py:line\`**` for file and line references
3. Reading the description and suggestion text
4. **Ignoring** the "What looks good" section
5. Recording prior Fixed/Resolved claims as status context, then checking current code before assigning an already-fixed or other disposition

If the latest comment is summary-only, use it as gate/status context. Keep
earlier aggregate findings and current line-specific findings in the ledger
until each has a verified disposition.

## Reply

There is no per-finding comment to reply to. Post a **single summary** as a new issue comment:

```markdown
## Addressed Aggregate Bot Review

Responding to review from [comment](link_to_comment):

| # | Severity | File:Line | Finding | Action |
|---|----------|-----------|---------|--------|
| 1 | P1 | auth.py:42 | Missing auth guard | Fixed |
| 2 | P2 | utils.py:50 | Unbounded memory | Fixed |
| 3 | P3 | types.py:10 | Any type annotation | Skipped - not in changed code |
```

## Re-flag priority

When a later round says previous findings are still unresolved, prioritize those items — they have been raised before.
