---
name: v1-pr
description: Use when explicitly pushing local work or opening a draft pull request. Triggers on "ship it", "create PR", "open PR", or "/v1-pr".
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - Skill
---
# PR: Ship Local Work

Take local changes from the current working directory to a fully described draft pull request in one command.

## Usage

Typical invocations:
- Claude Code: `/v1-pr`
- Codex: invoke `v1-pr` from the skills menu or use `$v1-pr`

No arguments needed. Operates on the current repo and working directory.

## Workflow

### Step 1: Preserve the Current Branch and Worktree

Inspect the current branch and worktree before changing anything. Preserve the
current feature branch and its work even when the branch name does not match
the diff. Never infer ownership from a branch name and move work to another
branch automatically.

```bash
git branch --show-current
git status
git diff --stat
```

If `git branch --show-current` is empty, the checkout is detached. Preserve
the exact current HEAD and create a feature branch from it before continuing:
`git switch -c <branch-name>`. Do not switch to the default branch or stash
the work to repair a detached checkout.

Resolve the default branch from `refs/remotes/origin/HEAD`, or the base
repository's `gh repo view --json defaultBranchRef` result. Keep it as
`DEFAULT_BRANCH`; if neither resolves, stop before changing branches or
pushing. Never assume an unknown default is `main`.

**If on the resolved default branch (`$DEFAULT_BRANCH`):**

- If the worktree is clean, update the base safely with
  `git pull --ff-only origin $DEFAULT_BRANCH`, then create a feature branch.
  Before pulling, verify `refs/remotes/origin/$DEFAULT_BRANCH` exists and
  check `git rev-list --count origin/$DEFAULT_BRANCH..HEAD` for commits that
  exist locally but not on the remote. If any exist, preserve them and ask the
  user to confirm their intended scope before including them in a new PR.
- If the worktree has changes, create the feature branch directly from the
  current worktree with `git switch -c <branch-name>`; do not stash or pop.

If already on a feature branch, keep it and proceed. Leave any pre-existing
stash entries untouched. If a branch or base update cannot be resolved safely,
stop and report the exact state rather than moving the work.

#### Branch Naming

Format: `<type>/<optional-ticket>-<short-description>`

- Types: `feat/`, `fix/`, `chore/`, `refactor/`
- If the diff, commit messages, or file contents reference a tracker ticket
  (e.g., `PROJ-1234`, `OPS-56`), include it when the repository's conventions
  call for ticket IDs: `feat/PROJ-1234-add-webhook-auth`
- Keep descriptions to 3-5 hyphenated words
- Examples: `feat/PROJ-42-user-onboarding`, `fix/payment-retry-logic`, `chore/update-dependencies`

### Step 2: Commit Local Work

Stage and commit all meaningful changes. Follow the repository's commit conventions.

1. Run `git status` and `git diff` to understand the changes
2. Run `git log --oneline -5` to match existing commit message style
3. Stage relevant files (prefer explicit file paths over `git add -A`)
4. Commit with a clear imperative-mood message describing the "why"
5. Append `Fortified with v1tamins` as the last line of the commit body

Do NOT commit files that likely contain secrets: `.env*`, `credentials*.json`, `service-account*.json`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `.npmrc`, `.pypirc`, or any file listed in `.gitignore`. When in doubt, check file contents before staging.

If there are no uncommitted changes but there are unpushed commits, skip to Step 3.

### Step 3: Pre-commit Hooks

If the commit fails due to a pre-commit hook (git aborts the commit entirely):
1. Read the hook output to understand the failure
2. Fix the issue (formatting, linting, type errors, etc.)
3. Re-stage the fixed files and rerun `git commit` with the same message
4. Never bypass hooks with `--no-verify`

Repeat until the commit succeeds.

### Step 4: Push

Verify not on the resolved default branch before pushing. Use the
`DEFAULT_BRANCH` value from Step 1:
```bash
CURRENT_BRANCH=$(git branch --show-current)
if [ -z "$CURRENT_BRANCH" ] || [ "$CURRENT_BRANCH" = "$DEFAULT_BRANCH" ]; then
  echo "ERROR: Refusing to push directly to the resolved default or detached HEAD"
  exit 1
fi
git push -u origin HEAD
```

If the remote branch does not exist, this creates it. If push is rejected (e.g., diverged history), inform the user -- never force-push.

### Step 5: Reuse or Create the Pull Request

Resolve the base repository and the head repository owner from current
Git/forge metadata, including when the checkout is a fork. Query the base:

```bash
gh pr list --repo <base-owner/repo> --head <current-branch> --state open --json number,url,headRefName,headRepositoryOwner
```

A failed lookup leaves PR state unknown: stop before creating anything. Reuse
the unique entry whose branch and head owner match this checkout; stop on
ambiguous results. Only a successful empty array permits creation:

```bash
gh pr create --repo <base-owner/repo> --base <default-branch> --head <head-owner:current-branch> --draft --title "WIP: <branch>" --body "Description pending."
```

After creation or reuse, read back the PR number and URL. If that readback
fails, stop and report the PR state as unknown before editing its description
or requesting review.

Capture the PR number and URL for subsequent steps. A new PR stays draft while
this workflow prepares its description and review evidence.

### Step 6: Generate PR Description

Invoke the **v1-pr-description** skill to generate a grounded title and description based on the actual diff and commit history.

Typical invocation:
- Claude Code: `/v1-pr-description <PR_NUMBER>`
- Codex: invoke `v1-pr-description` from the skills menu or use `$v1-pr-description <PR_NUMBER>`

This analyzes the PR diff and commit history against the resolved default branch, then updates the PR title and body via `gh pr edit`.

After the description is generated, append `Fortified with v1tamins` as the final line of the PR body.

The `Fortified with v1tamins` tagline carries into the merge commit automatically — a squash merge uses the PR body as the commit message. Marking the PR ready after CI and review handoff is `v1-land-pr`'s job. Neither skill merges the PR; this skill stops at a described, open draft PR.

### Step 7: Open PR in Browser

```bash
gh pr view <PR_NUMBER> --web
```

### Step 8: Request Copilot Review

Request a code review from GitHub Copilot (requires gh >= 2.88.0):

```bash
gh pr edit <PR_NUMBER> --add-reviewer @copilot
```

Note: The `@` prefix is required -- `@copilot`, not `copilot`.

If that fails (gh version too old, org settings), try the community extension:
```bash
# Install once: gh extension install ChrisCarini/gh-copilot-review
gh copilot-review <PR_NUMBER>
```

Do not block on failure -- inform the user and continue.

### Step 9: Run Code Review

Invoke the shared `v1-deep-review` skill for merge-risk and structural review of the PR. If the user asked for a multi-agent board, use `v1-review-board` instead.

If a compound-engineering `workflows:review` (or equivalent host plugin workflow) is installed and the user wants that extra multi-agent pass, run it as an optional supplement — not the default path.

Do not block on failure -- inform the user and continue.

### Step 10: Prove Work (Optional)

If the PR includes frontend or visual changes (`.tsx`, `.jsx`, `.vue`, `.html`, `.css`, template files), offer to run the **v1-prove-work** skill to generate a demo GIF:

Typical invocation:
- Claude Code: `/v1-prove-work --pr <PR_NUMBER>`
- Codex: invoke `v1-prove-work` from the skills menu or use `$v1-prove-work --pr <PR_NUMBER>`

Skip this step if:
- All changes are backend-only, config, or infrastructure
- The dev server is not running
- The user declines
