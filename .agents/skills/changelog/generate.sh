#!/bin/bash
set -e

echo "Write Changelog workflow activated."
echo ""

# Find latest changelog
echo "=== Finding Latest Changelog ==="
LATEST=$(ls -1 docs/internal/changelog/*.md 2>/dev/null | tail -1)
if [ -n "$LATEST" ]; then
  echo "Latest changelog: $LATEST"
  LATEST_DATE=$(basename "$LATEST" .md)
  echo "Date: $LATEST_DATE"
else
  echo "No previous changelogs found"
  LATEST_DATE="beginning"
fi

echo ""
echo "=== Fetching Recent PRs ==="
# List merged PRs since last changelog
gh pr list --state merged --limit 50 --json number,title,mergedAt,url

echo ""
echo "Ready to generate new changelog..."
