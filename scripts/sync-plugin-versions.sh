#!/usr/bin/env bash

# Mirror the version in package.json into both runtime plugin manifests so all
# three stay in lockstep. Run automatically by the `version` npm script after
# `changeset version` bumps package.json; safe to run by hand at any time.
#
# Two-phase: both manifests are rendered to temp files first, so a failure in
# either render aborts before any tracked file is touched; only after both
# render cleanly are they moved into place. A trap removes temp files on any
# exit, so a mid-run failure never leaves a stray temp or a half-applied bump.

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

codex_tmp="$(mktemp)"
claude_tmp="$(mktemp)"
trap 'rm -f "$codex_tmp" "$claude_tmp"' EXIT

# Phase 1 — render both manifests. If either jq fails, set -e aborts here and
# no tracked manifest has been touched.
jq --arg v "$version" '.version = $v' "$codex_manifest"  > "$codex_tmp"
jq --arg v "$version" '.version = $v' "$claude_manifest" > "$claude_tmp"

# Phase 2 — both rendered cleanly, so commit them.
mv "$codex_tmp" "$codex_manifest"
mv "$claude_tmp" "$claude_manifest"

echo "synced .codex-plugin/plugin.json and .claude-plugin/plugin.json -> $version"
