#!/usr/bin/env bash

# Mirror the version in package.json into both runtime plugin manifests so all
# three stay in lockstep. Run automatically by the `version` npm script after
# `changeset version` bumps package.json; safe to run by hand at any time.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
package_json="$repo_root/package.json"
codex_manifest="$repo_root/plugins/v1tamins/.codex-plugin/plugin.json"
claude_manifest="$repo_root/plugins/v1tamins/.claude-plugin/plugin.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required to sync plugin versions" >&2
  exit 1
fi

for f in "$package_json" "$codex_manifest" "$claude_manifest"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: missing file: $f" >&2
    exit 1
  fi
done

version="$(jq -r '.version' "$package_json")"
if [ -z "$version" ] || [ "$version" = "null" ]; then
  echo "ERROR: package.json has no version" >&2
  exit 1
fi

mirror() {
  local manifest="$1"
  local tmp
  tmp="$(mktemp)"
  jq --arg v "$version" '.version = $v' "$manifest" > "$tmp"
  mv "$tmp" "$manifest"
  echo "synced $(basename "$(dirname "$manifest")")/plugin.json -> $version"
}

mirror "$codex_manifest"
mirror "$claude_manifest"
