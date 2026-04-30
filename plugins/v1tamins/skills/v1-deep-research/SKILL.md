---
name: v1-deep-research
description: >
  Conducts multi-source deep research with iterative refinement and structured synthesis.
  Triggers on "deep research", "research report", "comprehensive analysis", "analyze X",
  "compare X vs Y", "state of the art", "what does the research say about".
  NOT for: simple lookups, debugging, questions answerable in 1-2 searches, code review.
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

Autonomous research skill that plans, executes multi-pass search, and synthesizes findings into structured reports with full source attribution.

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
| 3. SYNTHESIZE | Direct synthesis, no critique | Outline refinement + critique | Outline refinement + multi-persona critique + delta-queries |
| Target length | 2,000-4,000 words | 4,000-8,000 words | 8,000-15,000 words |
| Target sources | 8+ | 15+ | 25+ |

## Execution

**Step 0:** Run `date +%Y-%m-%d` to get the real current date. Use this date in all searches.

**Phase 1 -- PLAN:** Read `reference/methodology.md` and follow the PLAN phase instructions.

**Phase 2 -- RESEARCH:** Continue following `reference/methodology.md` RESEARCH phase.

**Phase 3 -- SYNTHESIZE:** Read `reference/report-assembly.md` for generation strategy. Read `reference/quality-gates.md` for validation standards. Follow the SYNTHESIZE phase in `reference/methodology.md`.

**Validation:** Resolve the bundled validator, then run it up to three times until the report passes:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

for dir in \
  "$REPO_ROOT/.agents/skills/deep-research" \
  "$REPO_ROOT/claude/skills/deep-research" \
  "${CLAUDE_PLUGIN_ROOT:-}" \
  "$HOME/.agents/skills/deep-research" \
  "$HOME/.codex/skills/deep-research" \
  "$HOME/.claude/skills/deep-research"; do
  [ -n "$dir" ] && [ -f "$dir/scripts/validate_report.py" ] && SKILL_ROOT="$dir" && break
done

if [ -z "${SKILL_ROOT:-}" ]; then
  echo "ERROR: Could not find scripts/validate_report.py" >&2
  exit 1
fi

python3 "$SKILL_ROOT/scripts/validate_report.py" --report [path]
```

## Output Contract

Reports MUST include:
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
