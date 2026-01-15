# Generate PR Description

## Overview

Create a comprehensive pull request description based on the changes in this branch relative to `main` branch, then **update the PR on GitHub** with the generated title and description.

## Input

The user should provide the GitHub PR URL, e.g.: `https://github.com/v1-io/abi/pull/123`

## Steps

1. **Analyze Changes**
    - Run `git diff main HEAD` to understand what changed
    - Review commit messages with `git log main..HEAD --oneline`

2. **Generate Title**
    - Provide a concise descriptive title for the PR (max 72 chars)

3. **Generate Description**
    - **Summary**: Clear, concise summary of what this PR accomplishes
    - **Changes Made**: List key changes (code and non-code), highlight breaking changes
    - **Testing**: Describe how changes were tested, include new test cases
    - **Related Issues**: Link to any related issues or tickets

4. **Update the PR on GitHub**
    - Use the GitHub CLI to update the PR title and body:
    ```bash
    gh pr edit <PR_NUMBER> --title "<TITLE>" --body "<BODY>"
    ```
    - If `gh` CLI is not available, provide the markdown for manual copy/paste

## Generate PR Description Checklist

- [ ] Analyzed git diff and commit history
- [ ] Generated concise descriptive title
- [ ] Generated complete description with summary, changes, testing, and related issues
- [ ] Highlighted any breaking changes
- [ ] **Updated the PR on GitHub using `gh pr edit`**
- [ ] Formatted as proper markdown
