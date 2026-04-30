#!/usr/bin/env bash
set -euo pipefail

pr_ref="${1:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI is required" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required" >&2
  exit 1
fi

if [ -z "$pr_ref" ]; then
  metadata="$(gh pr view --json number,url,title,body,baseRefName,headRefName,headRefOid,files,commits)"
else
  metadata="$(gh pr view "$pr_ref" --json number,url,title,body,baseRefName,headRefName,headRefOid,files,commits)"
fi

number="$(jq -r '.number' <<<"$metadata")"
url="$(jq -r '.url' <<<"$metadata")"
title="$(jq -r '.title' <<<"$metadata")"
base_ref="$(jq -r '.baseRefName' <<<"$metadata")"
head_ref="$(jq -r '.headRefName' <<<"$metadata")"
head_sha="$(jq -r '.headRefOid' <<<"$metadata")"
local_sha="$(git rev-parse HEAD 2>/dev/null || true)"

echo "=== PR ==="
echo "Number: $number"
echo "URL: $url"
echo "Title: $title"
echo "Base: $base_ref"
echo "Head: $head_ref"
echo "Head SHA: $head_sha"
if [ -n "$local_sha" ] && [ "$local_sha" != "$head_sha" ]; then
  echo "Warning: local HEAD ($local_sha) does not match PR head SHA"
fi
echo

echo "=== Current PR Body ==="
jq -r '.body // ""' <<<"$metadata"
echo

echo "=== Changed Files ==="
jq -r '.files[].path' <<<"$metadata"
echo

echo "=== Commits ==="
jq -r '.commits[] | "- \(.oid[0:12]) \(.messageHeadline)"' <<<"$metadata"
echo

if [ -z "$local_sha" ]; then
  echo "Warning: not in a git checkout; skipping local diff context" >&2
  exit 0
fi

if [ "$local_sha" != "$head_sha" ]; then
  echo "Warning: local HEAD does not match PR head; skipping local diff context" >&2
  exit 0
fi

git fetch origin "$base_ref" >/dev/null 2>&1 || true

merge_base=""
if git rev-parse --verify "origin/$base_ref" >/dev/null 2>&1; then
  merge_base="$(git merge-base "origin/$base_ref" HEAD 2>/dev/null || true)"
fi

if [ -n "$merge_base" ]; then
  echo "=== Diff Stat ($merge_base...HEAD) ==="
  git diff --stat "$merge_base"...HEAD
  echo

  echo "=== Diff Name Status ($merge_base...HEAD) ==="
  git diff --name-status "$merge_base"...HEAD
  echo

  echo "=== Commit Range ($merge_base..HEAD) ==="
  git log --oneline "$merge_base"..HEAD
else
  echo "Warning: could not compute merge base against origin/$base_ref" >&2
fi
