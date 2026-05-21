# Source Catalogue

Exact paths and commands for the sources scouted by this skill. All paths use `~/`. Session inspection is delegated to the compound-engineering plugin's `ce-session-inventory` and `ce-session-extract` primitives — this skill composes them rather than re-implementing JSONL parsing.

## Table of contents
- Source A: Merged PRs (GitHub)
- Source B+C: Agent sessions (Claude Code, Codex, Cursor)
- Existing solutions docs (for de-dup)

## Source A: Merged PRs (GitHub)

Repo: the repo of the current working directory (`gh` resolves it). Default base branch is `main`; override via `.agents/goldpan.config.yaml` (key: `pr_base_branch`).

For signal scoring (which sections, phrases, and diff patterns actually matter for *this* team), see the project's `.agents/goldpan-signals.md`. If absent, run calibration (see [calibration.md](calibration.md)) or fall back to the universal signals embedded in [scoring.md](scoring.md).

```bash
BASE_BRANCH="main"   # override from .agents/goldpan.config.yaml if present

gh pr list --state merged --base "$BASE_BRANCH" \
  --search "merged:>=<since_date>" \
  --json number,title,mergedAt,author,body,files \
  --limit 200

# For shortlisted PRs only — fetches commits + diff
gh pr view <number> --json body,commits,files
gh pr diff <number> | head -400
```

## Source B+C: Agent sessions (Claude Code, Codex, Cursor)

Single scout, three platforms. The compound-engineering plugin owns the platform-specific layout knowledge:

| Platform | Where it lives | Notes |
|---|---|---|
| Claude Code | `~/.claude/projects/<encoded-cwd>/` | Encoded as `cwd.replace('/', '-')`. Worktrees get a separate dir suffixed `--claude-worktrees-<branch>`. |
| Codex (active) | `~/.codex/sessions/YYYY/MM/DD/` | First line is `session_meta` with `payload.cwd`. |
| Codex (archived) | `~/.codex/archived_sessions/` | **Upstream `discover-sessions.sh` does NOT search this.** The wrapper script fills the gap. |
| Cursor | `~/.cursor/projects/<repo-folder>/agent-transcripts/` | No in-file timestamps; `ts` derived from mtime. |

### Discovery + ranking

The bundled wrapper handles all three platforms in one call, fills the archived-codex gap, and ranks sessions by compound-signal hit count via the upstream keyword filter:

```bash
bash <skill-path>/scripts/discover-sessions.sh <days>
```

Output is JSONL — one line per session that matched at least one keyword, plus a final `_meta` line with `files_processed`, `files_matched`, `parse_errors`. Each session line contains:

- `platform` — `claude` / `codex` / `cursor`
- `file` — absolute path
- `ts`, `last_ts` — start + last-message timestamps (Cursor uses mtime)
- `session` — session id
- `branch` — git branch (Claude only)
- `cwd` — working directory (Codex only)
- `match_count` — total compound-signal occurrences
- `keyword_matches` — per-keyword counts, e.g. `{"AIDEV-NOTE": 3, "Root Cause": 1, ...}`

The default keyword set is the universal compound signals. If the project's `.agents/goldpan-signals.md` lists additional verbatim phrases under "Verbatim phrases (sessions)", append them via the `COMPOUND_SIGNAL_KEYWORDS` env var:

```bash
COMPOUND_SIGNAL_KEYWORDS="AIDEV-NOTE,Root Cause,that worked,<your project's extra phrases>" \
  bash <skill-path>/scripts/discover-sessions.sh <days>
```

### Triage

1. Sort by `match_count` descending; cap to top ~20 per platform.
2. For each surviving session, match `branch` against Scout A's PR head branches — same-branch sessions are **supporting evidence** for that PR, not separate candidates.
3. Drop sessions whose `last_ts` is older than the window cutoff (mtime can be misleading after archiving).

### Deep-dive

For each shortlisted session, pull a filtered skeleton via `ce-session-extract` rather than reading raw JSONL:

```bash
CE_SKILLS_DIR="${CE_SKILLS_DIR:-}"
if [ -z "$CE_SKILLS_DIR" ]; then
  for dir in \
    "$HOME/.codex/plugins/cache/compound-engineering-plugin/compound-engineering"/*/skills; do
    [ -d "$dir/ce-session-extract/scripts" ] && CE_SKILLS_DIR="$dir" && break
  done
fi
if [ -z "$CE_SKILLS_DIR" ] && [ -d "$HOME/.claude/plugins" ]; then
  scripts_dir="$(find "$HOME/.claude/plugins" -path '*/compound-engineering/skills/ce-session-extract/scripts' -type d 2>/dev/null | sort | head -1)"
  [ -n "$scripts_dir" ] && CE_SKILLS_DIR="${scripts_dir%/ce-session-extract/scripts}"
fi
if [ -z "$CE_SKILLS_DIR" ]; then
  echo "ERROR: Could not find ce-session-extract" >&2
  exit 1
fi

EXT="$CE_SKILLS_DIR/ce-session-extract"

# Skeleton: user/assistant text + collapsed tool calls. Cap to last 200 lines.
cat <session-file> | python3 "$EXT/scripts/extract-skeleton.py" | tail -n 200

# Errors-only view: Claude `is_error: true` tool results, Codex non-zero exec_command_end events.
cat <session-file> | python3 "$EXT/scripts/extract-errors.py"
```

Skeleton output is one logical event per `---` block. Read it like a transcript — no JSON parsing needed in the scout. Most sessions reduce from MB-scale to ~1-3KB once filtered.

### Resolution signals (in skeleton output)

- Short user turns near the end: `that worked`, `it's fixed`, `working now`, `lgtm`, `ship it`
- Final assistant turn containing a PR URL → correlate with Source A
- Final assistant turn referencing the project's `docs/solutions/` path → already documented; demote candidate
- A `## Root Cause`-style section in an assistant message → strong knowledge
- Errors-mode output that converges on one error class → "what didn't work" material

### Anti-signals (drop the session candidate)

- Last user turn is a follow-up question or correction (resolution didn't land)
- Skeleton ends mid-tool-use (interrupted)
- All errors are missing-file or permissions noise (no learning)
- Branch matches a PR Scout A surfaced — fold into that PR's candidate

## Existing solutions docs (for de-dup)

Default path: `docs/solutions/` (matches `/ce-compound`'s default). Override via `.agents/goldpan.config.yaml` (key: `solutions_path`) — useful when the project keeps solutions in a vault outside the repo and symlinks them in, or routes them to a non-default location.

```bash
SOLUTIONS_PATH="docs/solutions"   # override from goldpan.config.yaml if present

grep -ril "<keyword>" "$SOLUTIONS_PATH"/ | head -10
grep -rE "^(component|tags|module): .*<keyword>" "$SOLUTIONS_PATH"/ | head
```

Categories follow ce-compound's schema: `best-practices`, `build-errors`, `database-issues`, `integration-issues`, `logic-errors`, `performance-issues`, `runtime-errors`, `security-issues`, `test-failures`, `ui-bugs`, plus knowledge-track categories (`architecture-patterns`, `design-patterns`, `tooling-decisions`, `conventions`, `workflow-issues`, `developer-experience`, `documentation-gaps`). New projects may not have all of these directories yet — `/ce-compound` creates them on first use of each category.

Decision rule: if a candidate's keywords match a file and the matched file's `## Problem` describes the same root cause, mark **covered** (move to "refresh candidates" section of the report).
