---
name: pr
description: Use when shipping local work as a pull request. Handles branch creation, committing, pushing, PR creation, description writing, Copilot review request, and multi-agent code review. Triggers on "ship it", "create PR", "open PR", "submit PR", "/pr".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - Skill
---

# PR: Ship Local Work

Take local changes from working directory to a fully described, reviewed pull request in one command.

## Usage

```
/pr
```

No arguments needed. Operates on the current repo and working directory.

## Workflow

### Step 1: Ensure Correct Branch

Determine the current branch state and ensure work is on an appropriately named feature branch.

```bash
git branch --show-current
git status
git diff --stat
```

Detect the default branch:
```bash
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
# Fallback if not set
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
```

**If on the default branch (`main` or `master`):**
1. Stash any uncommitted changes: `git stash`
2. Pull latest: `git pull origin $DEFAULT_BRANCH`
3. Infer a branch name from the staged/unstaged changes and stash (see "Branch Naming" below)
4. Check out the new branch: `git checkout -b <branch-name>`
5. Pop the stash: `git stash pop`

**If on a feature branch:**
Inspect the uncommitted changes and compare them to the branch name. If the branch name is clearly unrelated to the current work (e.g., branch is `feat/auth-flow` but all changes are in billing/), then:
1. Stash changes: `git stash`
2. Switch to the default branch and pull: `git checkout $DEFAULT_BRANCH && git pull origin $DEFAULT_BRANCH`
3. Create a new branch named for the actual work
4. Pop the stash: `git stash pop`

If the branch name reasonably matches the work, proceed.

#### Branch Naming

Format: `<type>/<optional-ticket>-<short-description>`

- Types: `feat/`, `fix/`, `chore/`, `refactor/`
- If the diff, commit messages, or file contents reference a Linear ticket (e.g., `VER-1234`, `HUM-56`), include it: `feat/VER-1234-add-webhook-auth`
- Keep descriptions to 3-5 hyphenated words
- Examples: `feat/VER-42-user-onboarding`, `fix/payment-retry-logic`, `chore/update-dependencies`

### Step 2: Commit Local Work

Stage and commit all meaningful changes. Follow the repository's commit conventions.

1. Run `git status` and `git diff` to understand the changes
2. Run `git log --oneline -5` to match existing commit message style
3. Stage relevant files (prefer explicit file paths over `git add -A`)
4. Commit with a clear imperative-mood message describing the "why"
5. Append `Fortified with v1tamins` as the last line of the commit body

Do NOT commit files that likely contain secrets (.env, credentials, tokens).

If there are no uncommitted changes but there are unpushed commits, skip to Step 3.

### Step 3: Pre-commit Hooks

If the commit fails due to a pre-commit hook (git aborts the commit entirely):
1. Read the hook output to understand the failure
2. Fix the issue (formatting, linting, type errors, etc.)
3. Re-stage the fixed files and rerun `git commit` with the same message
4. Never bypass hooks with `--no-verify`

Repeat until the commit succeeds.

### Step 4: Push

```bash
git push -u origin HEAD
```

If the remote branch does not exist, this creates it. If push is rejected (e.g., diverged history), inform the user -- never force-push.

### Step 5: Create the Pull Request

```bash
gh pr create --fill
```

Use `--fill` for an initial placeholder. The pr-description skill will overwrite it in the next step.

If a PR already exists for this branch, skip creation and capture the existing PR URL:
```bash
gh pr view --json url,number -q '.url + " " + (.number | tostring)'
```

Capture the PR number and URL for subsequent steps.

### Step 6: Generate PR Description

Invoke the **pr-description** skill to generate a grounded title and description based on the actual diff and commit history.

```
/pr-description <PR_NUMBER>
```

This analyzes `git diff main HEAD` and `git log main..HEAD`, then updates the PR title and body via `gh pr edit`.

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

### Step 9: Run Multi-Agent Code Review

Invoke the **compound-engineering workflows:review** skill for exhaustive multi-agent analysis:

```
/compound-engineering:workflows:review
```

This runs parallel review agents covering architecture, security, performance, patterns, and more.

If the skill is not available (not installed as a plugin), fall back to the in-repo `/code-review` skill instead. Do not block on failure -- inform the user and continue.

### Step 10: Prove Work (Optional)

If the PR includes frontend or visual changes (`.tsx`, `.jsx`, `.vue`, `.html`, `.css`, template files), offer to run the **prove-work** skill to generate a demo GIF:

```
/prove-work --pr <PR_NUMBER>
```

Skip this step if:
- All changes are backend-only, config, or infrastructure
- The dev server is not running
- The user declines

## Guidelines

- Never force-push. If push is rejected, inform the user.
- Never commit secrets or credentials.
- Never bypass pre-commit hooks with `--no-verify`.
- If any step fails, report the failure clearly and continue with remaining steps where possible.
- The PR description step is critical -- it grounds the PR in actual work, not placeholders.
- Prefer explicit file staging over blanket `git add -A`.
