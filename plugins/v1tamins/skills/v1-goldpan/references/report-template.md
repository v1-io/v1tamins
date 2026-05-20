# Report Template

Write the consolidated candidate list to `.agents/goldpan/session-notes/compound-candidates-<YYYY-MM-DD>.md`. Use this structure verbatim — only adjust counts.

```markdown
# Compound Candidates — <YYYY-MM-DD>

Window: last <N> days (since <YYYY-MM-DD>).
Sources scanned: PRs (<count>), Claude sessions (<count>), Codex sessions (<count>).

## High (worth /ce-compound today)

### 1. <Title>
- **Source**: PR #<n>, Claude session `<short-id>` (branch `<branch>`)
- **Track**: bug | knowledge
- **Suggested category**: `<category>/`
- **Component**: `<service-or-module>`
- **Synopsis**: 3-5 sentence summary of the problem, what didn't work, and how it was solved.
- **Why compound-worthy**: one sentence pointing at the non-obvious bit.
- **Existing coverage**: none | partial — see `<path>` (consider refresh)
- **Suggested invocation**: `/ce-compound <short context phrase>`

### 2. ...

## Medium (worth documenting eventually)

### 1. <Title>
- **Source**: ...
- **Synopsis**: 1-2 sentences.
- **Why deferred**: e.g. "overlap with existing doc", "fix shipped but rationale already in PR description".

## Already documented (refresh candidates)

For each, note the existing file and what new context the recent activity adds.

- `<existing-doc-path>` — new context: <one line>. Run `/ce-compound-refresh <scope>` if the new context contradicts or supersedes existing guidance.

## Skipped (audit trail)

Brief list of PRs/sessions considered but rejected, with one-word reason: `refactor`, `deps`, `unverified`, `trivial`, `wip`, `duplicate`.

- PR #<n>: refactor
- Codex session `<id>`: wip
- ...
```

## Inline chat output (after writing the file)

Show the user only the High section, condensed, then immediately move into Phase 4a (approval prompt). Do not stop — the queue step is part of the same turn.

```
Wrote <N> candidates to .agents/goldpan/session-notes/compound-candidates-<date>.md
(<H> High, <M> Medium, <D> already-documented refresh candidates).

High candidates:
1. <title> — track: <bug|knowledge>
2. <title> — track: <bug|knowledge>
3. <title> — track: <bug|knowledge>

(Phase 4a follows: which to queue through /ce-compound?)
```

Do not summarize Medium or Skipped sections in chat — those are in the file. Do not invoke `/ce-compound` until Phase 4a returns approvals.
