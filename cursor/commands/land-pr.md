# Land PR

## Overview

Commit, push, open, and land a pull request through CI handoff. Use this command when implementation work is done and the next goal is a review-ready pull request with passing CI.

## Input

The user can invoke this command without arguments from the repository containing the completed work:

```bash
/land-pr
```

## Steps

1. **Inspect Repository State**
   - Run `git status --short --branch`.
   - Identify the current branch, base branch, and changed files.
   - If the branch is `main` or another protected base branch, create a feature branch before committing.
   - Do not revert unrelated user changes. Leave unrelated changes unstaged unless the user clearly wants them included.

2. **Commit and Push**
   - Review the diff before committing with `git diff` and, when relevant, `git diff --staged`.
   - Run the fastest relevant local validation when it is clear from the changed files.
   - Stage only intended files.
   - Commit with a concise message that describes the user-visible or operational value.
   - Push the branch and set upstream if needed: `git push -u origin HEAD`.

3. **Open a Draft PR**
   - Reuse an existing PR for the branch when one exists.
   - Otherwise create one with `gh pr create --draft`.
   - Include a compact PR body with summary and validation.
   - Capture the PR number or URL with `gh pr view --json number,url,headRefName,baseRefName`.

4. **Monitor CI**
   - Poll with `gh pr checks <pr>`.
   - Use a 3 minute timeout per monitoring pass.
   - Treat required checks that are pending or running as wait conditions.
   - Treat failed, cancelled, timed out, action_required, or skipped required checks as failures to investigate.
   - If checks are inconclusive because GitHub has not created runs yet, wait briefly and poll again within the same timeout.

5. **Remediate Failed Checks**
   - Make up to three remediation pushes.
   - Inspect the failing check details before changing code. Prefer `gh run view --log-failed` or the failing job logs when available.
   - Fix the root cause locally.
   - Run the narrowest relevant validation that covers the failure.
   - Commit the fix and push.
   - Repeat the monitoring loop.
   - Stop after three remediation pushes if CI is still failing. Report the failing checks, what was attempted, and the latest PR URL.

6. **Mark Ready for Review**
   - When required checks pass, run `gh pr ready <pr>`.
   - Confirm the PR is no longer draft with `gh pr view <pr> --json isDraft,state,url`.

7. **Move Linear Ticket**
   - Look for a Linear issue key in the branch name, commit messages, PR title, or PR body.
   - If a Linear integration is available, move the matching issue to `Human Review`.
   - If no ticket is discoverable or Linear cannot be reached, do not block the PR; mention that the Linear handoff was skipped.

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

## Output

Report:

- PR URL and whether it is ready for review.
- Checks status.
- Number of remediation pushes used.
- Linear ticket status, if applicable.
- Any validation that could not be run.
