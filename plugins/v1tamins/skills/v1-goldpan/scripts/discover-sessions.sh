#!/usr/bin/env bash
# Thin wrapper around ce-session-inventory that:
#   1. Calls upstream discover-sessions.sh (Claude + Codex active + Cursor)
#   2. Adds the gap: ~/.codex/archived_sessions/ (upstream does not search this)
#   3. Pipes through ce-session-inventory's extract-metadata.py with a
#      compound-signal keyword set, so each session is ranked by how many
#      compound-worthy signals it contains.
#
# Usage:
#   discover-sessions.sh [days] [project-substring]
#
# Defaults:
#   days              = 7
#   project-substring = basename of $PWD (e.g. <home>/work/myrepo -> "myrepo")
#
# Output: JSONL (one session per line) plus a final _meta line. Each line
# carries match_count and keyword_matches; sessions with zero matches are
# excluded by extract-metadata.py.
#
# Override the keyword list with env COMPOUND_SIGNAL_KEYWORDS. Append project-
# specific phrases from .agents/goldpan-signals.md by setting that env var
# to the universal defaults plus your additions.
set -euo pipefail

DAYS="${1:-7}"

if [ -n "${2:-}" ]; then
  REPO="$2"
else
  REPO=$(basename "$PWD")
fi

resolve_ce_skills_dir() {
  local dir

  if [ -n "${CE_SKILLS_DIR:-}" ] && [ -d "$CE_SKILLS_DIR/ce-session-inventory/scripts" ]; then
    printf '%s\n' "$CE_SKILLS_DIR"
    return 0
  fi

  for dir in \
    "${HOME}/.codex/plugins/cache/compound-engineering-plugin/compound-engineering"/*/skills; do
    if [ -d "$dir/ce-session-inventory/scripts" ]; then
      printf '%s\n' "$dir"
      return 0
    fi
  done

  if [ -d "${HOME}/.claude/plugins" ]; then
    while IFS= read -r scripts_dir; do
      dir="${scripts_dir%/ce-session-inventory/scripts}"
      printf '%s\n' "$dir"
      return 0
    done < <(find "${HOME}/.claude/plugins" -path '*/compound-engineering/skills/ce-session-inventory/scripts' -type d 2>/dev/null | sort)
  fi

  return 1
}

CE_SKILLS_DIR="$(resolve_ce_skills_dir || true)"
INV_DIR="$CE_SKILLS_DIR/ce-session-inventory"
if [ -z "$CE_SKILLS_DIR" ]; then
  echo "ce-session-inventory not found in Codex or Claude plugin caches" >&2
  echo "Install the compound-engineering plugin and re-run." >&2
  exit 1
fi

# Universal compound-signal keyword set. These phrases generalize across
# teams and tend to mark moments where a real fix was confirmed or a root
# cause was named. Project-specific phrases (calibrated per team) should be
# appended via COMPOUND_SIGNAL_KEYWORDS — see .agents/goldpan-signals.md.
DEFAULT_KEYWORDS="AIDEV-NOTE,Root Cause,root cause,failure mode,that worked,it's fixed,working now,problem solved,ship it,lgtm"
KEYWORDS="${COMPOUND_SIGNAL_KEYWORDS:-$DEFAULT_KEYWORDS}"

(
  bash "$INV_DIR/scripts/discover-sessions.sh" "$REPO" "$DAYS"
  # Gap: archived Codex sessions (rotated out of ~/.codex/sessions/).
  if [ -d "${HOME}/.codex/archived_sessions" ]; then
    find "${HOME}/.codex/archived_sessions" \
      -name "rollout-*.jsonl" -mtime -"$DAYS" -type f 2>/dev/null
  fi
) \
| tr '\n' '\0' \
| xargs -0 python3 "$INV_DIR/scripts/extract-metadata.py" \
    --cwd-filter "$REPO" \
    --keyword "$KEYWORDS"
