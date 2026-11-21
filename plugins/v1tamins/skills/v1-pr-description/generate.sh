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

lower() {
  tr '[:upper:]' '[:lower:]' <<<"$1"
}

pr_coordinates_from_url() {
  local value="$1"
  local pattern='^https?://([a-zA-Z0-9.-]+)/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)/pull/0*([1-9][0-9]*)([/#?][^[:space:]]*)?$'
  if [[ "$value" =~ $pattern ]]; then
    printf '%s|%s|%s' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
    return 0
  fi
  return 1
}

remote_repository_identity() {
  local remote="$1"
  local remote_url=""
  local remote_host=""
  local remote_path=""

  # Fetch uses the first URL. Read it before Git applies url.*.insteadOf.
  remote_url="$(git config --get-all "remote.$remote.url" 2>/dev/null)" || return 1
  remote_url="${remote_url%%$'\n'*}"
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
  [[ "$remote_host" =~ ^[a-zA-Z0-9.-]+$ && "$remote_path" =~ ^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$ ]] || return 1
  printf '%s|%s' "$(lower "$remote_host")" "$(lower "$remote_path")"
}

unavailable() {
  echo "Diff context: unavailable ($1)" >&2
  exit 2
}

remote_mappings="$(
  while IFS= read -r remote; do
    [ -n "$remote" ] || continue
    remote_key="$(remote_repository_identity "$remote")" || continue
    printf '%s %s\n' "$remote_key" "$remote"
  done < <(git remote 2>/dev/null)
)"

matching_remotes() {
  local base_key="$1" key remote
  while read -r key remote; do
    if [ "$key" = "$base_key" ]; then
      printf '%s\n' "$remote"
    fi
  done <<<"$remote_mappings"
}

resolve_number_repository() {
  local repo_url default_repo repo_key
  local url_pattern='^https://([a-zA-Z0-9.-]+)/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)/?$'

  if [ -n "${GH_REPO:-}" ]; then
    repo_url="$(gh repo view "$GH_REPO" --json url --jq .url)" || return 1
  elif default_repo="$(gh repo set-default --view 2>/dev/null)" && [ -n "$default_repo" ]; then
    # The default's display name can omit its host. Read the canonical URL.
    repo_url="$(gh repo view --json url --jq .url)" || return 1
  else
    repo_key="$(cut -d ' ' -f 1 <<<"$remote_mappings" | sort -u)"
    [ -n "$repo_key" ] && [[ "$repo_key" != *$'\n'* ]] || return 1
    printf '%s' "$repo_key"
    return 0
  fi

  [[ "$repo_url" =~ $url_pattern ]] || return 1
  printf '%s|%s' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
}

requested_coordinates=""
if [ -z "$pr_ref" ]; then
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: no PR ref provided and current directory is not a git checkout" >&2
    usage
    exit 1
  fi
  if ! metadata="$(GH_PROMPT_DISABLED=1 gh pr view --json "$json_fields")"; then
    echo "Error: could not load PR metadata for the current branch; use a PR URL" >&2
    exit 1
  fi
else
  if [[ "$pr_ref" =~ ^#?0*([1-9][0-9]*)$ ]]; then
    requested_number="${BASH_REMATCH[1]}"
    if ! requested_repo="$(resolve_number_repository)"; then
      echo "Error: could not identify one base repository for PR #$requested_number; use a PR URL" >&2
      exit 1
    fi
  elif requested_coordinates="$(pr_coordinates_from_url "$pr_ref")"; then
    requested_number="${requested_coordinates##*|}"
    requested_repo="${requested_coordinates%|*}"
  else
    usage
    exit 1
  fi

  requested_coordinates="$requested_repo|$requested_number"
  repo_selector="${requested_repo%%|*}/${requested_repo#*|}"
  if [ -z "$(matching_remotes "$(lower "$requested_repo")")" ]; then
    unavailable "no local remote maps to GitHub base repository ${requested_repo#*|} on ${requested_repo%%|*}"
  fi
  if ! metadata="$(gh pr view --repo "$repo_selector" --json "$json_fields" -- "$requested_number")"; then
    echo "Error: could not load PR #$requested_number from $repo_selector" >&2
    exit 1
  fi
fi

number="$(jq -r '.number // ""' <<<"$metadata")"
url="$(jq -r '.url // ""' <<<"$metadata")"
if ! returned_coordinates="$(pr_coordinates_from_url "$url")"; then
  unavailable "PR metadata did not include a supported GitHub pull request URL"
fi
if [ "$number" != "${returned_coordinates##*|}" ] ||
   { [ -n "$requested_coordinates" ] &&
     [ "$(lower "$requested_coordinates")" != "$(lower "$returned_coordinates")" ]; }; then
  unavailable "returned PR URL does not match the requested repository and number"
fi

pr_repo="${returned_coordinates%|*}"
pr_host="${pr_repo%%|*}"
pr_repository="${pr_repo#*|}"
repo_selector="$pr_host/$pr_repository"
base_repository_key="$(lower "$pr_repo")"
base_remotes="$(matching_remotes "$base_repository_key")"
if [ -z "$base_remotes" ]; then
  unavailable "no local remote maps to GitHub base repository $pr_repository on $pr_host"
fi

title="$(jq -r '.title // ""' <<<"$metadata")"
base_ref="$(jq -r '.baseRefName // ""' <<<"$metadata")"
pr_base_sha="$(jq -r '.baseRefOid // ""' <<<"$metadata")"
base_sha=""
head_ref="$(jq -r '.headRefName // ""' <<<"$metadata")"
head_sha="$(jq -r '.headRefOid // ""' <<<"$metadata")"
head_repo="$(jq -r '.headRepository.nameWithOwner // .headRepositoryOwner.login // "unavailable"' <<<"$metadata")"
local_sha="$(git rev-parse HEAD 2>/dev/null || true)"
base_repository=""
identity_error=""
if ! repository_metadata="$(gh repo view "$repo_selector" --json id,nameWithOwner 2>/dev/null)"; then
  identity_error="could not load GitHub repository identity for $repo_selector"
elif ! base_repository="$(jq -er '.nameWithOwner // empty' <<<"$repository_metadata")"; then
  identity_error="GitHub repository metadata did not include nameWithOwner"
elif ! base_repository_id="$(jq -er '.id // empty' <<<"$repository_metadata")"; then
  identity_error="GitHub repository metadata did not include id"
elif [ "$(lower "$base_repository")" != "$(lower "$pr_repository")" ]; then
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

if [ "$local_sha" != "$head_sha" ] || [ -z "$local_sha" ]; then
  unavailable "local HEAD does not match PR head SHA"
fi

if [ -n "$identity_error" ]; then
  unavailable "$identity_error"
fi

base_remote=""
while IFS= read -r remote; do
  if [ "$(remote_repository_identity "$remote" || true)" != "$base_repository_key" ]; then
    continue
  fi

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
done <<<"$base_remotes"

if [ -z "$base_remote" ]; then
  unavailable "the mapped base remote could not prove base SHA $base_sha"
fi

echo "=== Diff Stat ($base_sha...$head_sha) ==="
git diff --stat "$base_sha...$head_sha"
echo

echo "=== Diff Name Status ($base_sha...$head_sha) ==="
git diff --name-status "$base_sha...$head_sha"
echo

echo "=== Commit Range ($base_sha..$head_sha) ==="
git log --oneline "$base_sha..$head_sha"
