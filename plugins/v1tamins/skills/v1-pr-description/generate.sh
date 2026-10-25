#!/usr/bin/env bash
set -euo pipefail

pr_ref="${1:-}"
json_fields="number,url,title,body,baseRefName,baseRefOid,headRefName,headRefOid,headRepository,headRepositoryOwner,files,commits"

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

number="$(jq -r '.number // ""' <<<"$metadata")"
url="$(jq -r '.url // ""' <<<"$metadata")"
title="$(jq -r '.title // ""' <<<"$metadata")"
base_ref="$(jq -r '.baseRefName // ""' <<<"$metadata")"
pr_base_sha="$(jq -r '.baseRefOid // ""' <<<"$metadata")"
base_sha=""
head_ref="$(jq -r '.headRefName // ""' <<<"$metadata")"
head_sha="$(jq -r '.headRefOid // ""' <<<"$metadata")"
head_repo="$(jq -r '.headRepository.nameWithOwner // .headRepositoryOwner.login // "unavailable"' <<<"$metadata")"
local_sha="$(git rev-parse HEAD 2>/dev/null || true)"

lower() {
  tr '[:upper:]' '[:lower:]' <<<"$1"
}

pr_repository_from_url() {
  local value="$1"
  if [[ "$value" =~ ^https://([^/]+)/([^/]+)/([^/]+)/pull/[0-9]+/?$ ]]; then
    printf '%s|%s/%s' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
    return 0
  fi
  return 1
}

remote_repository_identity() {
  local remote="$1"
  local remote_url=""
  local remote_host=""
  local remote_path=""

  # `git remote get-url` applies url.*.insteadOf rewrites. Read the raw
  # configured URL so identity checks cannot be redirected to another repo.
  remote_url="$(git config --get "remote.$remote.url" 2>/dev/null || true)"
  [ -n "$remote_url" ] || return 1

  case "$remote_url" in
    https://*|http://*)
      remote_host="${remote_url#*://}"
      remote_host="${remote_host%%/*}"
      remote_path="${remote_url#*://*/}"
      ;;
    ssh://*)
      remote_host="${remote_url#ssh://}"
      remote_host="${remote_host%%/*}"
      remote_host="${remote_host#*@}"
      remote_path="${remote_url#ssh://*/}"
      ;;
    git@*:*)
      remote_host="${remote_url#git@}"
      remote_host="${remote_host%%:*}"
      remote_path="${remote_url#*:}"
      ;;
    file://*|/*|./*|../*)
      remote_host="local"
      remote_path="${remote_url#file://}"
      remote_path="${remote_path##*/}"
      ;;
    *)
      return 1
      ;;
  esac

  remote_path="${remote_path%%\?*}"
  remote_path="${remote_path%%#*}"
  remote_path="${remote_path%/}"
  remote_path="${remote_path%.git}"
  remote_path="${remote_path#/}"
  remote_path="${remote_path%/}"
  [ -n "$remote_host" ] && [ -n "$remote_path" ] || return 1
  printf '%s|%s' "$(lower "$remote_host")" "$(lower "$remote_path")"
}

base_repository_key=""
base_repository=""
identity_error=""
if ! parsed_pr_repository="$(pr_repository_from_url "$url")"; then
  identity_error="PR URL is not a supported GitHub repository URL"
else
  pr_host="${parsed_pr_repository%%|*}"
  pr_repository_from_url="${parsed_pr_repository#*|}"
  repo_selector="$pr_host/$pr_repository_from_url"
  if ! repository_metadata="$(gh repo view "$repo_selector" --json id,nameWithOwner 2>/dev/null)"; then
    identity_error="could not load GitHub repository identity for $repo_selector"
  elif ! base_repository="$(jq -er '.nameWithOwner // empty' <<<"$repository_metadata")"; then
    identity_error="GitHub repository metadata did not include nameWithOwner"
  elif ! base_repository_id="$(jq -er '.id // empty' <<<"$repository_metadata")"; then
    identity_error="GitHub repository metadata did not include id"
  elif [ "$(lower "$base_repository")" != "$(lower "$pr_repository_from_url")" ]; then
    identity_error="GitHub repository identity did not match the PR URL"
  elif [ -z "$base_ref" ]; then
    identity_error="PR metadata did not include the base branch name"
  else
    base_ref_endpoint="repos/$base_repository/git/ref/heads/$base_ref"
    if ! base_ref_metadata="$(gh api --hostname "$pr_host" "$base_ref_endpoint" 2>/dev/null)"; then
      identity_error="could not resolve the authoritative base ref from $pr_host"
    elif ! live_base_ref="$(jq -er '.ref // empty' <<<"$base_ref_metadata")"; then
      identity_error="base ref API response did not include ref"
    elif [ "$live_base_ref" != "refs/heads/$base_ref" ]; then
      identity_error="base ref API response did not match the requested branch"
    elif ! live_base_sha="$(jq -er 'select(.object.type == "commit") | .object.sha // empty' <<<"$base_ref_metadata")"; then
      identity_error="base ref API response did not include a commit SHA"
    elif [[ ! "$live_base_sha" =~ ^[0-9a-fA-F]{40}$ ]]; then
      identity_error="base ref API response included an invalid commit SHA"
    elif ! repository_metadata_after="$(gh repo view "$repo_selector" --json id,nameWithOwner 2>/dev/null)"; then
      identity_error="could not re-read GitHub repository identity after resolving the base ref"
    elif ! base_repository_after="$(jq -er '.nameWithOwner // empty' <<<"$repository_metadata_after")"; then
      identity_error="GitHub repository re-read did not include nameWithOwner"
    elif ! base_repository_id_after="$(jq -er '.id // empty' <<<"$repository_metadata_after")"; then
      identity_error="GitHub repository re-read did not include id"
    elif [ "$(lower "$base_repository_after")" != "$(lower "$base_repository")" ] || [ "$base_repository_id_after" != "$base_repository_id" ]; then
      identity_error="GitHub repository identity changed while resolving the base ref"
    else
      base_sha="$live_base_sha"
      base_repository_key="$(lower "$pr_host|$base_repository")"
    fi
  fi
fi

echo "=== PR ==="
echo "Number: $number"
echo "URL: $url"
echo "Title: $title"
echo "Base: $base_ref"
echo "Base repository: ${base_repository:-unavailable}"
echo "Base SHA: ${base_sha:-unavailable}"
echo "PR metadata base SHA (historical): ${pr_base_sha:-unavailable}"
echo "Head: $head_ref"
echo "Head SHA: $head_sha"
echo "Head repository: $head_repo"
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
  echo "Diff context: unavailable (not in a git checkout)" >&2
  exit 2
fi

if [ "$local_sha" != "$head_sha" ]; then
  echo "Diff context: unavailable (local HEAD does not match PR head SHA)" >&2
  exit 2
fi

base_remote=""
if [ -n "$identity_error" ]; then
  echo "Diff context: unavailable ($identity_error)" >&2
  exit 2
fi

if [ -z "$base_ref" ] || [ -z "$base_sha" ]; then
  echo "Diff context: unavailable (PR metadata did not include base branch and base SHA)" >&2
  exit 2
fi

matching_remote_found=0
remotes="$(git remote 2>/dev/null || true)"
while IFS= read -r remote; do
  [ -n "$remote" ] || continue
  remote_key="$(remote_repository_identity "$remote" || true)"
  if [ "$remote_key" != "$base_repository_key" ]; then
    continue
  fi
  matching_remote_found=1

  if ! git fetch --no-tags "$remote" -- "refs/heads/$base_ref" >/dev/null 2>&1; then
    echo "Warning: could not fetch $base_ref from the PR base remote '$remote'" >&2
    continue
  fi

  fetched_base_sha="$(git rev-parse --verify --quiet FETCH_HEAD^{commit} 2>/dev/null || true)"
  if [ "$fetched_base_sha" != "$base_sha" ]; then
    echo "Warning: fetched $remote/$base_ref resolved to ${fetched_base_sha:-unavailable}, expected $base_sha" >&2
    continue
  fi

  if ! git cat-file -e "$base_sha^{commit}" 2>/dev/null; then
    echo "Warning: fetched base SHA $base_sha is not available as a commit" >&2
    continue
  fi

  base_remote="$remote"
  break
done <<<"$remotes"

if [ -z "$base_remote" ]; then
  if [ "$matching_remote_found" -eq 0 ]; then
    echo "Diff context: unavailable (no local remote maps to GitHub base repository $base_repository)" >&2
  else
    echo "Diff context: unavailable (the mapped base remote could not prove base SHA $base_sha)" >&2
  fi
  exit 2
fi

if [ -n "$base_remote" ]; then
  echo "=== Diff Stat ($base_sha...HEAD) ==="
  git diff --stat "$base_sha"...HEAD
  echo

  echo "=== Diff Name Status ($base_sha...HEAD) ==="
  git diff --name-status "$base_sha"...HEAD
  echo

  echo "=== Commit Range ($base_sha..HEAD) ==="
  git log --oneline "$base_sha"..HEAD
fi
