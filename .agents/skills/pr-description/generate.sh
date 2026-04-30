#!/usr/bin/env bash
set -euo pipefail

pr_ref="${1:-}"
json_fields="number,url,title,body,baseRefName,headRefName,headRefOid,files,commits"

usage() {
  echo "Usage: $0 <PR_URL_or_NUMBER>" >&2
  echo "       $0  # from a git checkout with a current-branch PR" >&2
}

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI is required" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required" >&2
  exit 1
fi

if [ -z "$pr_ref" ]; then
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: no PR ref provided and current directory is not a git checkout" >&2
    usage
    exit 1
  fi

  if ! metadata="$(gh pr view --json "$json_fields")"; then
    echo "Error: could not load PR metadata for the current branch" >&2
    usage
    exit 1
  fi
else
  if ! metadata="$(gh pr view --json "$json_fields" -- "$pr_ref")"; then
    echo "Error: could not load PR metadata for: $pr_ref" >&2
    usage
    exit 1
  fi
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

merge_base=""
base_remote=""
stale_base_remote=""
for remote in upstream origin; do
  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    continue
  fi

  if git fetch "$remote" -- "$base_ref" >/dev/null 2>&1; then
    if git rev-parse --verify --quiet "refs/remotes/$remote/$base_ref^{commit}" >/dev/null; then
      base_remote="$remote"
      break
    fi
  else
    echo "Warning: could not fetch $remote/$base_ref" >&2
    if [ -z "$stale_base_remote" ] && git rev-parse --verify --quiet "refs/remotes/$remote/$base_ref^{commit}" >/dev/null; then
      stale_base_remote="$remote"
    fi
  fi
done

if [ -z "$base_remote" ] && [ -n "$stale_base_remote" ]; then
  base_remote="$stale_base_remote"
  echo "Warning: using existing local refs/remotes/$base_remote/$base_ref; it may be stale" >&2
fi

if [ -n "$base_remote" ]; then
  merge_base="$(git merge-base "refs/remotes/$base_remote/$base_ref" HEAD 2>/dev/null || true)"
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
  echo "Warning: could not compute merge base against a fetched $base_ref remote branch" >&2
fi
