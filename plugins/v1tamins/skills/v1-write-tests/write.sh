#!/bin/bash
set -e

TARGET=$1

echo "Write Unit Tests workflow activated."
echo ""

if [ -z "$TARGET" ]; then
  default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')"
  if [ -z "$default_branch" ]; then
    default_branch="main"
  fi
  echo "Analyzing changes between current branch and $default_branch..."
  git diff "origin/$default_branch...HEAD" --name-only
else
  echo "Target: $TARGET"
fi

echo ""
echo "Will add focused tests for changed behavior using project conventions."
