---
name: v1-land-pr
description: Open a draft PR or get a branch ready for review. Explicit workflow for commit, push, PR creation, CI, and review feedback.
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
  - Write
  - Skill
---

# Prepare a PR for Review

## Overview

Commit and push the intended changes, open or reuse a pull request, and take
it through CI and review handoff. Start new PRs as drafts. If the user requests
a draft only, stop with a verified, described draft. Otherwise continue until
the PR is ready for human review. Never merge it.

## Input

The user can invoke this command without arguments from the repository containing the completed work:

```bash
/v1-land-pr
```

For an orchestrated or resumed run, accept the caller's
`remediation_pushes_used` (integer 0–3). A genuinely new standalone run starts
at zero. A resumed run must recover the existing count from its caller or
prior handoff; if it is unknown, stop before another remediation push rather
than reset it. Return the cumulative count and latest head on every exit,
including blocked or failed exits, so the caller can carry the same limit
through another review cycle. No new state file is required.

## Steps

1. **Inspect Repository State**
   - Run `git status --short --branch`.
   - Identify the current branch, changed files, and intended base and head repositories from the Git remotes and GitHub metadata. In a fork, verify the upstream base and the fork that will receive the push. Use the full PR URL for subsequent PR operations.
   - Look for an open PR in the base repository. Run `gh pr list --repo <host/owner/repo> --head <branch> --state open --json url,headRefName,headRepository,baseRefName,isDraft`. Filter by the exact head branch and repository that match the intended push destination. Reuse a unique match. Stop if the lookup fails or more than one match remains. If the user requests a draft only and the matching PR is already open for review, report its state before making any changes.
   - Resolve the PR base branch in this order:
     1. Reuse the base branch from an existing PR for the current branch.
     2. Honor an explicit base branch requested by the user.
     3. Read the default branch of the verified base repository with `gh repo view <host/owner/repo> --json defaultBranchRef` or the configured HEAD of the matching base remote.
     4. If neither source resolves a configured default branch, stop before changing branches, committing, pushing, or creating a PR. Never guess `main`, `master`, or another base branch.
   - Do not assume a staging, release, or environment-specific branch exists. If the base branch cannot be determined, or branch choice has release-routing implications, ask the user before creating the PR.
   - Preserve the current feature branch. For a detached checkout, create a feature branch from the current HEAD without stashing the work. On the default branch, intended base, `main`, `master`, or a protected branch, check for local-only commits against the fetched remote branch before creating a feature branch. Confirm scope before carrying any local-only commits from such a branch. If there is nothing to ship, stop. Follow repository branch naming conventions and preserve uncommitted changes.
   - Do not revert unrelated user changes. Leave unrelated changes unstaged unless the user clearly wants them included.

2. **Commit and Push**
   - Review the diff before committing with `git diff` and, when relevant, `git diff --staged`.
   - Run the fastest relevant local validation when it is clear from the changed files.
   - Resolve the push destination from the existing PR's head repository and branch, including fork PRs; verify a matching Git remote and fetch that head branch. For a new PR, use the intended branch on the verified repository remote. Do not assume `origin` is an existing PR's head repository.
   - For an existing PR, require the fetched remote head to match its recorded `headRefOid` before using it for comparison. If that remote, branch, or SHA cannot be verified, stop and report the missing comparison. A verified absent branch for a new PR has no remote head to compare and can be created by the push below.
   - If the worktree is clean and local `HEAD` matches the fetched head, skip staging, committing, and pushing. Never create an empty commit or no-op push.
   - When a remote head exists, a local-ahead branch is expected: allow the push when `git merge-base --is-ancestor <fetched-head> HEAD` succeeds. If the local branch is behind or diverged, stop and report both SHAs; integrate remote commits only within the user's authorization.
   - Re-read the existing PR head immediately before pushing. If it changed from the fetched head, refresh the comparison before proceeding.
   - Never force-push. If a push is rejected, stop and report the rejection.
   - Count remediation consistently at every push site, including this step on a resumed run. Initial publication of a clean implementation is not a remediation push; a push containing fixes for already observed check/review failures is, even if those commits were prepared during another review cycle.
   - Before any remediation push, require a known cumulative count below three. At three, stop before publishing pending remediation commits. After a successful remediation push, increment exactly once and retain the updated count before entering monitoring or returning to the caller; do not reinitialize it in the CI loop.
   - Stage only intended files and verify the staged diff excludes secrets and unrelated work.
   - Commit with a concise message that describes the user-visible or operational value. If a commit hook fails, correct the failure and retry without bypassing the hook.
   - Push to the verified head destination and set upstream if needed: `git push -u <head-remote> HEAD:<head-branch>`.

3. **Open or Reuse the PR**
   - Repeat the exact PR lookup for the pushed head, including the branch owner and repository. Only a successful lookup with no matching open PR permits creation. If an existing PR was requested as a draft-only result and is already open for review, report that state without changing it.
   - For a new PR, use `v1-pr-description` to draft the visual title and body against the verified revisions and PR template. Create it with `gh pr create --repo <host/base-owner/repo> --base <base-branch> --head <head-owner:head-branch> --draft --title "<title>" --body-file <body-file>`. Use the unqualified head branch for a same-repository PR.
   - Read back the selected PR by URL with `gh pr view <pr-url> --json number,url,baseRefName,headRefName,headRefOid,headRepository,isDraft,title,body`. Verify the target, the pushed head SHA, and the draft state and description for a new PR. Stop if the result cannot be verified. If a reused draft has an empty or stale description, pass its URL to `v1-pr-description` and update it within the user's authorization.
   - Return now for a draft-only request. Otherwise keep a new PR in draft while checks and review feedback are pending.

4. **Monitor CI & Code Review**
   - Poll checks with `gh pr checks <pr>`.
   - On every monitoring pass, invoke `v1-address-review` to build a complete review ledger. Do not rely on `gh pr view --json comments,reviews` alone because it does not expose every inline comment, aggregate bot report, check annotation, or review-thread state.
   - Inspect every available feedback surface: submitted reviews, line-specific review comments, PR-level issue comments, unresolved review threads, aggregate bot reports or status comments, and feedback or annotations attached to checks.
   - Use a 3 minute timeout per monitoring pass.
   - Treat required checks that are pending or running as wait conditions.
   - Treat failed, cancelled, timed out, action_required, or skipped required checks as failures to investigate.
   - Treat feedback from every actor identically for discovery and disposition. This includes humans and automated reviewers such as Codex, Copilot, Code Factory, Datadog, GitHub Actions, security scanners, linters, and other installed apps or bots. Never filter feedback by author, actor type, bot name, severity, or whether it appears in a review, comment, or check.
   - Classify every finding as valid, partial, invalid, duplicate, already fixed, or blocked. Every finding requires a recorded disposition even when it does not require a code change.
   - If checks are inconclusive because GitHub has not created runs yet, wait briefly and poll again within the same timeout.
   - Record the PR head SHA used to build the ledger. If the head changes, rebuild the ledger before replying, resolving threads, or declaring review complete.

5. **Remediate Failed Checks and Code Review Feedback**
   - Make up to three cumulative remediation pushes, including pushes already used in earlier invocations of this run.
   - Inspect the failing check details before changing code. Prefer `gh run view --log-failed` or the failing job logs when available.
   - Remediate every valid or partial finding regardless of source. For invalid, duplicate, or already-fixed findings, verify the current code and explain the disposition instead of silently skipping the feedback.
   - Investigate failing checks from their concrete output before changing code; use the narrowest relevant debugging or review workflow.
   - Reply to every review item, including items that require no code change. Use an inline reply for line comments and a summary reply for aggregate bot reports or PR-level feedback.
   - Resolve every review thread whose finding is fixed, already fixed, duplicate and covered, or confirmed invalid. Leave a thread open only when work is partial or blocked, a reviewer answer is required, or the current code still leaves reasonable ambiguity; record the exact reason in the ledger.
   - Repeat the monitoring loop. Invoke `v1-address-review` after every remediation push and use `v1-debug` for failing checks as needed.
   - Stop after three remediation pushes if CI is still failing. Report the failing checks, what was attempted, and the latest PR URL.

6. **Run the Final Review Audit**
   - After the latest head's checks and automated reviews finish, fetch all feedback surfaces again and rebuild the ledger against that head SHA. A remediation push can trigger new bot feedback, so an earlier clean ledger is not sufficient.
   - Verify that every discovered item has a disposition and reply, every valid or partial item is remediated or explicitly blocked, and every thread eligible for resolution reports `isResolved: true`.
   - Do not mark the PR ready or report review completion while an unaddressed item or resolvable open thread remains.
   - If GitHub API access, pagination, permissions, or tooling prevents a complete audit or thread resolution, fail closed: keep the PR in draft and report the exact blocker. Do not treat an incomplete feedback inventory as zero feedback.
   - When the final audit passes, mark a draft ready with `gh pr ready <pr-url>`. For a PR already open for review, proceed directly to readback. Require `gh pr view <pr-url> --json number,url,headRefOid,isDraft` to show the audited head SHA and `isDraft: false`. If the command or readback fails or the head does not match, report readiness as unverified.

## CI Loop

Use three remediation attempts, not three polling attempts:

```text
# remediation_pushes was resolved at intake and includes any Step 2 remediation push
while remediation_pushes <= 3:
  monitor checks and all feedback surfaces for up to 3 minutes
  if required checks passed and the final review audit passed:
    mark the PR ready if it is draft, then verify the current head plus `isDraft: false` by readback
    if the user explicitly requested tracker handoff and repository instructions identify a configured tracker:
      update that configured tracker through its documented route and verify readback
    else:
      leave external tracker state unchanged and report that
    stop
  if checks are still pending after timeout:
    continue monitoring unless progress is clearly stuck
  inspect check failures and undispositioned feedback
  if remediation_pushes == 3:
    stop and report failure
  fix valid findings, reply, resolve eligible threads, validate, commit, push
  remediation_pushes += 1
  return the updated count and new head to the caller before any review/resume boundary
```

Do not make speculative fixes without reading the failing check output. If the failure is unrelated to the branch, flaky, or infrastructure-owned, rerun the failed job once if appropriate and report the evidence instead of churning code.

## Definition of Done

For a draft-only request, verify the PR and draft state at Step 3 and report
that CI and review follow-through remain pending. For the full workflow:

- All required checks passed, or three remediation pushes were used and the remaining failures were reported without claiming the PR is ready.
- The final ledger covers all human and automated feedback surfaces against the latest PR head SHA.
- Every feedback item has a recorded disposition and a reply, regardless of source or whether it required a code change.
- Every valid or partial finding was remediated and validated, or is explicitly blocked with the exact reason.
- Every review thread eligible for resolution is verified resolved; any intentionally open thread has a recorded reason.
- The PR is marked ready only when checks pass, no feedback item is unaddressed, and no resolvable review thread remains open.
- The workflow never merges the PR.

## Output

Report:

- PR URL and whether it remains draft or is ready for review.
- Checks status.
- Review ledger totals by disposition, reply status, and thread resolution status.
- Cumulative number of remediation pushes used and remaining, plus the latest head SHA.
- Configured tracker status only when explicitly requested; otherwise state that it was unchanged.
- Any validation, feedback inventory, reply, or thread resolution that could not be completed.
