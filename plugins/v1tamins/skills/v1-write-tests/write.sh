#!/bin/bash
set -e

TARGET=$1

echo "Write Unit Tests workflow activated."
echo ""

if [ -z "$TARGET" ]; then
  echo "Analyzing changes between current branch and main..."
  git diff main HEAD --name-only
else
  echo "Target: $TARGET"
fi

echo ""
echo "Will create comprehensive unit tests following project conventions."
