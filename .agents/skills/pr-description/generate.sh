#!/bin/bash
set -e

PR_INPUT=$1

if [ -z "$PR_INPUT" ]; then
  echo "Error: PR URL or number required"
  echo "Usage: /pr-description <PR_URL_or_NUMBER>"
  echo ""
  echo "Examples:"
  echo "  /pr-description https://github.com/v1-io/abi/pull/123"
  echo "  /pr-description 123"
  exit 1
fi

# Extract PR number if URL provided
if [[ $PR_INPUT =~ /pull/([0-9]+) ]]; then
  PR_NUMBER="${BASH_REMATCH[1]}"
else
  PR_NUMBER="$PR_INPUT"
fi

echo "Analyzing changes for PR #${PR_NUMBER}..."
echo ""

# Show the git diff and logs
echo "=== Git Diff ==="
git diff main HEAD

echo ""
echo "=== Commit History ==="
git log main..HEAD --oneline

echo ""
echo "PR Number: ${PR_NUMBER}"
echo "Ready to generate description..."
