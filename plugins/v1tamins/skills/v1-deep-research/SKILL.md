---
name: v1-deep-research
description: Use when conducting multi-source research with structured synthesis. Triggers on "deep research", "research report", or "compare the state of the art".
allowed-tools:
  - WebSearch
  - WebFetch
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
---
# Deep Research

Plan the search, run it in passes, and write a cited report.

## Decision Tree

```
User request
  |
  ├─ Answerable in 1-2 searches? ──> STOP. Use WebSearch directly.
  ├─ Debugging or code question? ──> STOP. Use Explore agent or Read tool.
  ├─ "Compare X vs Y" detected? ──> COMPARISON mode (see methodology.md)
  └─ Research question ──> Select mode:
       ├─ User says "quick" or simple topic ──> QUICK
       ├─ Default ──> STANDARD
       └─ User says "deep" or "thorough" ──> DEEP
```

## Modes

| Phase | Quick | Standard | Deep |
|-------|-------|----------|------|
| 1. PLAN | 2 orientation searches, 3 sub-queries | 2 orientation searches, 5 sub-queries | 3 orientation searches, 7 sub-queries |
| 2. RESEARCH | Parallel sub-queries only | + 2 sub-agents + 1 gap-fill round | + 3 sub-agents + 2 gap-fill rounds + source curation |
| 3. SYNTHESIZE | Direct synthesis, no critique | Outline refinement + critique | Outline refinement + three-angle critique + delta-queries |
| Target sources | 8+ | 15+ | 25+ |

Length follows evidence: Quick answers the question; Standard and Deep cover every sub-question with cited evidence.

## Execution

**Step 0:** Run `date +%Y-%m-%d` for the real current date. Use that date in every search.

**Phase 1 -- PLAN:** Read `reference/methodology.md` and follow the PLAN phase.

**Phase 2 -- RESEARCH:** Keep following `reference/methodology.md` for the RESEARCH phase.

**Phase 3 -- SYNTHESIZE:** Read `reference/report-assembly.md` for how to write the report. Read `reference/quality-gates.md` for what has to pass. Follow the SYNTHESIZE phase in `reference/methodology.md`.

**Validation:** Resolve the bundled validator, then run it up to three times until the report passes:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RESOLVER=""
for candidate in \
  "$REPO_ROOT/plugins/v1tamins/scripts/resolve-skill-root.sh" \
  "${CLAUDE_PLUGIN_ROOT:-}/scripts/resolve-skill-root.sh" \
  "$HOME/.claude/skills/v1-deep-research/../../scripts/resolve-skill-root.sh" \
  "$HOME/.codex/skills/v1-deep-research/../../scripts/resolve-skill-root.sh" \
  "$HOME/.claude/plugins/cache"/*/v1tamins/*/scripts/resolve-skill-root.sh \
  "$HOME/.codex/plugins/cache/v1tamins/v1tamins"/*/scripts/resolve-skill-root.sh; do
  [ -x "$candidate" ] && RESOLVER="$candidate" && break
done
if [ -z "${RESOLVER:-}" ]; then
  echo "ERROR: Could not find resolve-skill-root.sh" >&2
  exit 1
fi
SKILL_ROOT="$("$RESOLVER" v1-deep-research scripts/validate_report.py)"

python3 "$SKILL_ROOT/scripts/validate_report.py" --report [path]
```

## Output Contract

Every report includes:
- Executive Summary (200-400 words, standalone, no citations)
- Structured body sections with inline citations `[N]`
- Methodology note (what was searched, how many sources, date range)
- Limitations / gaps acknowledged
- Bibliography with numbered entries matching inline citations
- All sources hyperlinked

Output location: `~/Documents/Research/[Topic]_[YYYYMMDD]/report.md`

## Flags

- `--quick` / `--deep` -- override mode selection
- `--context` -- emit compact summary for other skills (no full report)
- `--compare` -- force comparison mode for "X vs Y" queries
