#!/usr/bin/env bash
# Thin wrapper around compound-engineering's session scripts that:
#   1. Calls upstream discover-sessions.sh (Claude + Codex active + Cursor)
#   2. Adds the gap: ~/.codex/archived_sessions/ (upstream does not search this)
#   3. Pipes through upstream's extract-metadata.py with a compound-signal
#      keyword set, so each session is ranked by how many compound-worthy
#      signals it contains.
#
# The upstream scripts have moved between compound-engineering releases
# (ce-session-inventory/ce-session-extract -> ce-sessions -> ce-compound/
# scripts/session-history); find_ce_script() locates each script by basename
# across every known layout in both the Claude and Codex plugin caches.
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

# Locate a compound-engineering session script by basename across every layout
# the plugin has shipped, preferring the newest installed version:
#   legacy:  <skills>/ce-session-inventory/scripts/  +  <skills>/ce-session-extract/scripts/
#   3.13.x:  <skills>/ce-sessions/scripts/                 (consolidated into one skill)
#   3.15.x:  <skills>/ce-compound/scripts/session-history/ (moved under ce-compound)
# A given install may carry only a subset of the four scripts under any one
# layout, so each script is resolved independently. Honors $CE_SKILLS_DIR
# (a compound-engineering "skills" dir) as an override.
find_ce_script() {
  local script="$1" rel p
  local rels=(
    "ce-session-inventory/scripts/$script"
    "ce-session-extract/scripts/$script"
    "ce-sessions/scripts/$script"
    "ce-compound/scripts/session-history/$script"
  )

  if [ -n "${CE_SKILLS_DIR:-}" ]; then
    for rel in "${rels[@]}"; do
      [ -f "$CE_SKILLS_DIR/$rel" ] && { printf '%s\n' "$CE_SKILLS_DIR/$rel"; return 0; }
    done
  fi

  local roots=()
  [ -d "${HOME}/.codex/plugins/cache" ] && roots+=("${HOME}/.codex/plugins/cache")
  [ -d "${HOME}/.claude/plugins/cache" ] && roots+=("${HOME}/.claude/plugins/cache")
  [ ${#roots[@]} -eq 0 ] && return 1

  p="$(
    find "${roots[@]}" -type f -name "$script" 2>/dev/null \
      | grep -E "/compound-engineering/[^/]+/skills/(ce-session-inventory|ce-session-extract|ce-sessions)/scripts/${script}$|/compound-engineering/[^/]+/skills/ce-compound/scripts/session-history/${script}$" \
      | sort -V | tail -n1 || true
  )"
  [ -n "$p" ] && { printf '%s\n' "$p"; return 0; }
  return 1
}

ce_not_found() {
  echo "compound-engineering session script '$1' not found." >&2
  echo "Searched ce-session-inventory / ce-session-extract (legacy), ce-sessions (3.13.x)," >&2
  echo "and ce-compound/scripts/session-history (3.15.x) under ~/.claude and ~/.codex plugin caches." >&2
  echo "Install or upgrade the compound-engineering plugin, or set CE_SKILLS_DIR to its skills dir." >&2
  exit 1
}

DISCOVER="$(find_ce_script discover-sessions.sh || true)"
[ -n "$DISCOVER" ] || ce_not_found discover-sessions.sh

# Keep extract-metadata.py coherent with the discover script when they ship
# together (legacy + 3.13.x); fall back to a global search otherwise.
discover_dir="$(dirname "$DISCOVER")"
if [ -f "$discover_dir/extract-metadata.py" ]; then
  EXTRACT_META="$discover_dir/extract-metadata.py"
else
  EXTRACT_META="$(find_ce_script extract-metadata.py || true)"
fi
[ -n "$EXTRACT_META" ] || ce_not_found extract-metadata.py

# Universal compound-signal keyword set. These phrases generalize across
# teams and tend to mark moments where a real fix was confirmed or a root
# cause was named. Project-specific phrases (calibrated per team) should be
# appended via COMPOUND_SIGNAL_KEYWORDS — see .agents/goldpan-signals.md.
DEFAULT_KEYWORDS="AIDEV-NOTE,Root Cause,root cause,failure mode,that worked,it's fixed,working now,problem solved,ship it,lgtm"
KEYWORDS="${COMPOUND_SIGNAL_KEYWORDS:-$DEFAULT_KEYWORDS}"

(
  bash "$DISCOVER" "$REPO" "$DAYS"
  # Gap: archived Codex sessions (rotated out of ~/.codex/sessions/).
  if [ -d "${HOME}/.codex/archived_sessions" ]; then
    find "${HOME}/.codex/archived_sessions" \
      -name "rollout-*.jsonl" -mtime -"$DAYS" -type f 2>/dev/null
  fi
) \
| tr '\n' '\0' \
| xargs -0 python3 "$EXTRACT_META" \
    --cwd-filter "$REPO" \
    --keyword "$KEYWORDS"
