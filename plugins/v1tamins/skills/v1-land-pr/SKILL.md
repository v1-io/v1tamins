---
name: v1-land-pr
description: "Commit, push, open, and land a pull request through CI handoff. Use when work is complete and the user wants an agent to create or update a PR, open it as a draft, monitor GitHub checks with `gh pr checks`, fix failed checks, retry up to three remediation pushes, mark the PR ready for review once green, and move a linked Linear ticket to Human Review when one exists. Trigger on requests like 'land this PR', 'open and monitor a PR', 'commit push and watch CI', 'get this ready for review', or 'finish the PR workflow'."
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
  - Write
---

# Land PR

## Overview

Commit, push, open, and land a pull request through CI handoff. Use this command when implementation work is done and the next goal is a review-ready pull request with passing CI.

## Input

The user can invoke this command without arguments from the repository containing the completed work:

```bash
/v1-land-pr
```

## Steps

1. **Inspect Repository State**
   - Run `git status --short --branch`.
   - Identify the current branch, changed files, and intended PR base branch.
   - Resolve the PR base branch in this order:
     1. Reuse the base branch from an existing PR for the current branch.
     2. Honor an explicit base branch requested by the user.
     3. Detect the repository default branch with `gh repo view --json defaultBranchRef` or `git remote show origin`.
     4. Fall back to a local `main` or `master` only when remote/default metadata is unavailable.
   - Do not assume a staging, release, or environment-specific branch exists. If the base branch cannot be determined, or branch choice has release-routing implications, ask the user before creating the PR.
   - If the branch is `main` or another protected base branch, create a feature branch before committing.
   - Do not revert unrelated user changes. Leave unrelated changes unstaged unless the user clearly wants them included.

2. **Commit and Push**
   - Review the diff before committing with `git diff` and, when relevant, `git diff --staged`.
   - Run the fastest relevant local validation when it is clear from the changed files.
   - Stage only intended files.
   - Commit with a concise message that describes the user-visible or operational value.
   - Push the branch and set upstream if needed: `git push -u origin HEAD`.

3. **Open a PR**
   - Reuse an existing PR for the branch when one exists.
   - Otherwise create one with `gh pr create`.
   - Pass the resolved base branch explicitly when creating a new PR.
   - Include a PR body with summary, a walkthrough of the changes, and validation steps taken. Where possible, invoke the **v1-pr-description** skill to generate the PR body.
   - Capture the PR number or URL with `gh pr view --json number,url,headRefName,baseRefName`.

4. **Monitor CI & Code Review**
   - Poll with `gh pr checks <pr>` and `gh pr view <pr> --json comments,reviews`.
   - Use a 3 minute timeout per monitoring pass.
   - Treat required checks that are pending or running as wait conditions.
   - Treat failed, cancelled, timed out, action_required, or skipped required checks as failures to investigate.
   - If checks are inconclusive because GitHub has not created runs yet, wait briefly and poll again within the same timeout.
   - While polling, check for code review comments from both humans and bot reviewers.

5. **Remediate Failed Checks and Code Review Feedback**
   - Make up to three remediation pushes.
   - Inspect the failing check details before changing code. Prefer `gh run view --log-failed` or the failing job logs when available.
   - Inspect review feedback and comments from human and bot reviewers.
   - Use subagents to identify root cause(s), fix them locally with the narrowest possible changes, and push the fix.
   - Reply to comments and close those that are resolved by the fix.
   - Repeat the monitoring loop. Use the **v1-address-review** and **v1-debug** skills as needed.
   - Stop after three remediation pushes if CI is still failing. Report the failing checks, what was attempted, and the latest PR URL.

## CI Loop

Use three remediation attempts, not three polling attempts:

```text
remediation_pushes = 0
while remediation_pushes <= 3:
  monitor gh pr checks for up to 3 minutes
  if all required checks passed:
    mark ready and update Linear
    stop
  if checks are still pending after timeout:
    continue monitoring unless progress is clearly stuck
  inspect failures
  if remediation_pushes == 3:
    stop and report failure
  fix, validate, commit, push
  remediation_pushes += 1
```

Do not make speculative fixes without reading the failing check output. If the failure is unrelated to the branch, flaky, or infrastructure-owned, rerun the failed job once if appropriate and report the evidence instead of churning code.

## Definition of Done
- All required checks passed OR 3 remediation pushes were used
- All code review comments addressed
- All code review comments replied to
- All code review comments that led to a code change were resolved

## Output

Report:

- PR URL and whether it is ready for review.
- Checks status.
- Number of remediation pushes used.
- Linear ticket status, if applicable.
- Any validation that could not be run.
