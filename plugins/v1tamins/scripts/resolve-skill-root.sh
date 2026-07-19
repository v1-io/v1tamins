#!/usr/bin/env bash
# Resolve the install root of a v1tamins skill by locating a marker file.
# Usage: resolve-skill-root.sh <skill-name> <marker-relpath>
# Prints the absolute skill directory on success; exits 1 on failure.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <skill-name> <marker-relpath>" >&2
  exit 2
fi

skill_name="$1"
marker="$2"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

candidates=(
  "$repo_root/plugins/v1tamins/skills/$skill_name"
  "${CLAUDE_PLUGIN_ROOT:-}/skills/$skill_name"
  "$HOME/.codex/skills/$skill_name"
  "$HOME/.claude/skills/$skill_name"
)

# Codex / Claude plugin caches (versioned installs)
shopt -s nullglob
for dir in \
  "$HOME/.codex/plugins/cache/v1tamins/v1tamins"/*/skills/"$skill_name" \
  "$HOME/.claude/plugins/cache"/*/v1tamins/*/skills/"$skill_name"; do
  candidates+=("$dir")
done
shopt -u nullglob

for dir in "${candidates[@]}"; do
  if [[ -f "$dir/$marker" && -f "$dir/SKILL.md" ]]; then
    printf '%s\n' "$dir"
    exit 0
  fi
done

echo "ERROR: Could not find $skill_name marker $marker" >&2
exit 1
