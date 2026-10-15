---
name: v1-deep-review
description: Use when reviewing a PR or branch for merge risk or maintainability. Triggers on "review this PR", "code review", or "maintainability audit".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Skill
---
# Deep Review

Review any pull request, branch, or change — code, docs, config, or mixed — on two bars:

- **Merge risk:** is it correct, complete, and safe to merge? Bugs, regressions, missing requirements, security, data, tests, scope drift.
- **Structural maintainability:** does it leave the codebase simpler to change? Abstraction quality, spaghetti/branching growth, file-size boundaries, type/ownership cleanliness.

Default mode is review-only. Apply fixes only when the user explicitly asks for "review and fix", "fix review findings", or a shipping workflow clearly requested code changes.

## Usage

Typical invocations:
- Claude Code: `/v1-deep-review <PR_URL_or_NUMBER>` or `/v1-deep-review` to review the current branch
- Codex: invoke `v1-deep-review` from the skills menu or use `$v1-deep-review <PR_URL_or_NUMBER>`

Examples:
```bash
/v1-deep-review https://github.com/your-org/your-repo/pull/123
/v1-deep-review 123
/v1-deep-review
/v1-deep-review --post
/v1-deep-review --fix
```

For a multi-agent review across peer runtimes, use `v1-review-board`. To respond to review comments already posted on a PR, use `v1-address-review`.

## Operating Rules

- Lead with findings, ordered by severity. Keep summaries secondary.
- Cite exact `file_path:line_number` for every finding.
- Review the full diff before commenting. Do not flag issues already fixed elsewhere in the same diff.
- Only report real, actionable problems. Skip style preferences unless they hide a bug or maintainability risk.
- Verify claims by reading code. Do not say "probably", "likely handled", or "should be fine" without evidence.
- Do not post to GitHub unless the user used `--post`, explicitly asked to post, or the existing workflow clearly expects posting. Otherwise return review text in chat.
- Do not modify code in default review mode.

## The Two Bars

Both bars run by default on code changes. Steps 1-5 below establish context and cover the **merge-risk** bar. Step 6 applies the **structural** bar. For a pure docs/config PR, run the merge-risk bar adapted (correctness, completeness vs intent, broken links/refs, cross-doc consistency) and mark the structural bar not applicable.

If the user's request is explicitly and only about structure ("maintainability audit", "architecture review"), lead with the structural bar but still sanity-check merge risk. If it is explicitly and only about merge risk ("review for bugs before merge"), lead with merge risk and apply structure as a secondary lens.

## Workflow

### 1. Resolve Target

Record the repository, requested scope, base and head commit SHAs, and the
merge-base used for the comparison. Keep those revisions fixed during the audit.

For a PR, read its requirements and revision metadata first:
```bash
gh pr view <PR> --json url,title,body,author,baseRefName,baseRefOid,headRefName,headRefOid,labels
```

Resolve the base repository from the PR URL and the head from `headRefOid`,
including fork PRs. Obtain the pinned commit objects through the matching
repository remote or approved provider interface. Compare the merge-base of
those commits with the pinned head. Read source from that head, for example
`git show <head-sha>:<path>`. Use an isolated checkout when execution needs it;
preserve the user's current branch and uncommitted work. Local files and tests
are evidence only when they match the reviewed snapshot. If only a live provider
diff is available, read revision metadata before and after retrieval and accept
it only if both base and head still match. Defer existing review discussion to
step 7.

For the current branch, establish local state:
```bash
git status --short
git branch --show-current
git rev-parse HEAD
git symbolic-ref --short refs/remotes/origin/HEAD
```

Use the requested base, otherwise resolve the repository's default branch from
its remote or provider metadata. Fetch missing refs from the verified repository
when permitted. If the base cannot be resolved, report the missing comparison
instead of assuming `main`. By default a branch review covers committed changes;
state that staged, unstaged, and untracked changes are excluded. Include them
only when requested, recording their diff/content snapshot separately from the
commit SHAs. For a requested file subset, record that narrower scope explicitly.

Build a compact changed-path inventory from the pinned comparison. Mark each
path reviewed, skipped with reason, or unavailable; account for renamed,
deleted, binary, and generated files as applicable. Recover truncated diffs or
missing context before declaring coverage complete. If required evidence remains
unavailable, name the affected paths/contracts and mark the affected bar
incomplete. “No findings” describes the inspected evidence only. Never use
destructive git commands to obtain coverage.

### 2. Establish Stated Intent

Extract what the work claims to do from the PR title/body, commit messages, branch name, `TODOS.md`, recent files in `docs/plans/` or `docs/brainstorms/`, and any Linear/Jira references. Produce a one-line intent summary before reviewing:

```markdown
Intent: <what this branch appears to be trying to accomplish>
Changed surface: <main files/modules touched>
Risk flags: <auth/data/API/async/UI/migrations/external services/tests/docs>
```

### 3. Scope Drift And Completion Audit

Compare stated intent against the diff. Check for scope creep (unrelated refactors, unmentioned behavior, files outside the expected surface), missing requirements, partial implementation (code not wired, tests without production code, UI without backend or vice versa), and test gaps.

If a plan file is found, classify each actionable item as `[DONE]` / `[PARTIAL]` / `[NOT DONE]` / `[CHANGED]`. Keep this audit concise — informational unless a missing item causes a real bug or user-facing gap.

### 4. Build Repo-Aware Understanding

For each meaningful changed file: read surrounding code, imports, callers, and contracts; search repo-wide for usage (`rg "<Symbol>" -n`); read nearby tests and fixtures; check `AGENTS.md`, `CLAUDE.md`, README, and local docs. Align findings with existing patterns before proposing new abstractions.

### 5. Merge-Risk Passes

Run these as lenses, not separate reports.

**Always run:**
- **Correctness:** logic errors, boundary cases, state transitions, idempotency, error propagation
- **Testing:** missing negative-path tests, edge cases, isolation, flakiness, weak assertions
- **Maintainability (surface):** dead code, stale comments, unnecessary abstractions, duplicated logic, unclear naming (deep structural review is step 6)

**Run when applicable:**
- **Security:** auth/authz, input validation, secrets, injection, SSRF, unsafe rendering
- **Data/migrations:** rollback safety, data loss, locking, backfills, indexes, mixed-version deploys
- **Performance:** N+1 queries, unbounded loops/queries, algorithmic complexity, bundle size, blocking I/O
- **API contracts:** response shape changes, status codes, versioning, pagination, webhook payloads
- **Frontend/UI:** async races, loading/error/empty states, accessibility, responsive behavior, console errors
- **External services/LLM:** trust boundaries, schema validation, retries, timeouts, rate limits, cost controls

When a UI change crosses an API, service client, state hook, or server route boundary, build a contract matrix before writing findings:

| Layer | File(s) | Contract to verify | Tests/evidence |
| --- | --- | --- | --- |
| API route or handler | `...` | auth, status codes, request/response shape, pagination, timeout/abort behavior | `...` |
| Service client | `...` | typed inputs/outputs, error mapping, retry/abort behavior | `...` |
| State hook/store | `...` | loading, empty, stale, error, optimistic update, cancellation | `...` |
| Component/view | `...` | rendered states, accessibility, responsive layout, destructive-action affordances | `...` |

Use the matrix to catch half-wired work.

When a consequential change depends on a specific safety claim, state that
claim and trace the relevant boundary. Check serialized consumers,
persistence, dependency behavior, or timing when the diff makes them relevant.
Use the cheapest meaningful execution of actual code to resolve the claim:
an existing test may suffice; a small reproduction may resolve a remaining
uncertainty. Respect review-only mode and execution authority; do not mutate
production or external systems to obtain proof. If execution is unavailable,
distinguish source-supported reasoning from an unproven premise in Verification.
A citation is not execution evidence, and a passing focused check does not
prove deployment. Skip this step when the change has no consequential safety
premise; do not add an exhaustive consumer search or require new tests by default.

After the passes, do one adversarial pass:

> Think like an attacker, a chaos engineer, and a hostile QA tester. What fails under load, bad input, retries, concurrency, stale state, partial failure, or confused users?

### 6. Structural Pass

For code changes, apply the structural maintainability bar. **Load [references/structural-review.md](references/structural-review.md)** and use it as a lens: does the change leave the codebase simpler to change, or add avoidable concepts, branches, files, casts, wrappers, and ownership leaks? It carries the deep-module / code-judo rubric, the >1000-line file blocker, "define errors out of existence", the structural finding shape, and the structural approval bar. Skip for pure docs/config PRs.

### 7. Reconcile Existing Reviews

Finish both independent passes and record candidate findings before reading
other reviewers' conclusions. Then, for a PR, read existing review bodies,
inline review conversations, and relevant human/bot discussion through the
repository's approved interface. Paginate to cover that discussion even when
the independent audit found nothing. Requirements in the PR body may be read
earlier; reviewer conclusions are deferred where practical. If prior feedback
was already supplied, disclose that the pass was not independent.

Check each relevant external finding against the pinned source. Incorporate and
attribute valid findings, deduplicate overlap, and discard findings already
fixed at that revision. Repetition or reviewer agreement does not increase
confidence without evidence. If discussion cannot be read, report that
reconciliation is incomplete without discarding the independent findings.

### 8. Finding Gates And Verdicts

Severity: **Critical** (likely production bug, security, data loss, broken core flow, unsafe migration, or a structural regression that will force a costly rewrite) · **High** (serious edge case, regression, missing required behavior, or file-size/spaghetti explosion) · **Medium** (maintainability/test/UX gap that can cause future bugs) · **Low/Nit** (minor, clearly actionable, low-noise only).

Confidence gates: 4-5/5 include in main findings; 3/5 include only with explicit uncertainty; 1-2/5 do not include.

Merge-risk findings use this shape:
```markdown
[ID] [Severity] file_path:line_number - Short title
Bar: Merge risk
Disposition: Blocking | Nonblocking improvement
Problem: What is wrong and when it fails.
Impact: Why it matters.
Fix: Concrete change to make.
Test: Specific test or verification to add/run.
Confidence: N/5.
```

Structural findings use the shape in `references/structural-review.md`. If no issues are found, say so clearly and mention residual risk or unverified areas.

Give each finding a stable ID and identify its bar and whether it blocks merge
or is a nonblocking improvement. Blocking findings need concrete impact;
security/correctness failures take precedence over optional restructuring.
Apply the structural approval bar to demonstrated structural regressions.

Report a separate verdict for each bar:

- **Acceptable:** applicable coverage is complete and no blocking finding remains.
- **Blocked:** cite the IDs of established blocking findings. Still disclose any
  incomplete coverage; a known blocker does not imply a complete audit.
- **Incomplete:** no blocker is established, but missing revision, source, or
  verification evidence prevents a supported decision. Name what is missing.
- **Not applicable:** only when that bar is skipped under The Two Bars; explain why.

Keep discussion-reconciliation coverage separate from the two verdicts. Missing
discussion leaves the overall PR review incomplete even if both independent
bars are acceptable. Never present incomplete coverage as unconditional approval.

### 9. Fix-First Mode

Only when the user explicitly asks to fix findings. Classify: **AUTO-FIX** (mechanical, local, low-risk, no product judgment) vs **ASK** (behavior change, architecture choice, migration, public API change, security-sensitive, broad refactor, or uncertain). Apply AUTO-FIX items with `Edit`, then report `[AUTO-FIXED] file_path:line_number - Problem -> fix applied`. Batch ASK items in one concise question. Do not commit, push, or create PRs from this skill.

If tests are already failing, invoke or recommend `v1-fix-tests`. If the issue is missing coverage, invoke or recommend `v1-write-tests` after the user approves adding tests.

After fixes, review the resulting snapshot and record its revision or local
diff/content snapshot. Report updated local finding dispositions and both local
verdicts separately from the pinned PR-head verdicts. A fix present only in the
working tree does not clear a finding on the remote head. Update the PR-head
verdicts only after the fixes exist at a verified remote head and the affected
source and checks have been reviewed there. Do not commit or push from this skill.

### 10. Output

Label verdicts by snapshot. When reporting both PR-head and local-fix results,
use separate verdict blocks; the local block is explicitly unpublished.

```markdown
## Findings

<severity-ordered findings across both bars, or "No findings.">

## Verdicts

Snapshot: <PR head SHA / committed branch SHA / local content snapshot (unpublished)>
Merge risk: <Acceptable / Blocked (finding IDs) / Incomplete (missing evidence)>
Structural maintainability: <Acceptable / Blocked (finding IDs) / Incomplete / Not applicable (reason)>

## Open Questions

<only questions that affect review confidence or implementation safety>

## Scope Check

Intent: ...
Delivered: ...
Drift/missing work: ...
Reviewed snapshot: <repository; base/head/merge-base SHAs; included local changes or file subset>
Coverage: <reviewed paths; skipped/unavailable paths and reasons>
Review discussion: <reconciled / incomplete with reason / not applicable>

## Verification

Tests/checks reviewed or run:
- ...

Residual risk:
- ...
```

Keep the final summary short. Findings are the product.

### 11. Posting To GitHub

When posting is requested:

1. Re-read PR base/head metadata and compare with the reviewed snapshot. If
   either changed, refresh the affected diff, source, findings, and verdicts
   before posting. For included local changes, recheck their recorded content.
   If the new snapshot cannot be verified, report the review as stale and stop
   before posting findings against it.
   Publish only findings and verdicts for that verified PR head. If local fixes
   are absent from it, retain the remote findings and verdicts; describe local
   progress separately as unpublished, without substituting its verdicts.
2. Request changes for high-confidence blocking findings. If coverage is
   incomplete without a confirmed blocker, post a comment naming the gaps;
   missing evidence alone is not a defect. Otherwise post a comment review.
3. Post only high-confidence findings, with the reviewed revisions and coverage
   limits. Do not post speculative notes or imply approval from an incomplete review.
4. Prefer one consolidated review body over many noisy comments unless line-level comments are specifically useful.

```bash
gh pr review <PR> --request-changes -b "$(cat /tmp/review.md)"
gh pr review <PR> --comment -b "$(cat /tmp/review.md)"
```

## Anti-Patterns

- Do not request tests without naming the behavior that must be protected.
- Do not soften a major maintainability regression into a mild suggestion.
- Do not post secrets, private logs, or sensitive data in GitHub comments.
