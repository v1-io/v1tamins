# PR Signals Template

This file is the structure that the calibration workflow ([calibration.md](calibration.md)) writes to `.agents/goldpan-signals.md` in the user's project. It is also the format to use when manually authoring or editing a project's signals file.

The signals file's role: capture verbatim, project-specific evidence — section headings, phrases, file-path patterns, author cohorts, calibration PRs — that scouts use to score candidates against *this team's* writing style. The universal compound-worthiness rubric lives in [scoring.md](scoring.md); this file is the per-project complement.

## Template

Copy the block below into `.agents/goldpan-signals.md` and fill in the placeholders. Or run `/v1-goldpan recalibrate` to have it auto-generated from your last 30 days of merged PRs.

```markdown
# <Project> PR Signals (grounded in <N> merges, <YYYY-MM-DD> → <YYYY-MM-DD>)

Verbatim signals derived from a four-agent calibration pass over the last 30 days of merges. Pass this file to Scout A so it scores against real evidence, not assumed language.

## Table of contents
- Author cohorts (filter by who shipped it)
- Strong positive signals (body)
- Strong positive signals (diff)
- Strong positive signals (title)
- Anti-signals (auto-skip)
- High-leverage subsystem paths
- Tempting-but-routine traps
- Calibration PRs (sanity check set)

## Author cohorts

| Author | Share | Compound rate | Bias |
|---|---|---|---|
| `<author1>` | <X>% | ~<Y>% | <one-line note about what's typical for this author> |
| `<author2>` | <X>% | ~<Y>% | <one-line note> |
| `<author3>` | <X>% | ~<Y>% | <one-line note> |

Always include author in the candidate output. Cohort-aware thresholds: a thin body from a high-compound-rate author may still be a candidate; a thin body from a low-compound-rate bot rarely is.

## Strong positive signals (body)

### Verbatim section headings (high signal)

List the exact `## ...` headers that, when present, correlate with compound-worthy work in this project. Quote the heading verbatim:

- `<## Heading actually observed in PR bodies>`
- `<## Another heading>`
- ...

### Verbatim phrases

List exact phrases (quoted) that appear in compound-worthy PR bodies for this team:

- `<exact phrase from PR body>`
- `<another phrase>`
- ...

## Strong positive signals (diff)

The diff often reveals what the body buries. Check these even when the body looks thin.

| Diff signal | Implication |
|---|---|
| <signal — e.g. "Adds ≥1 `AIDEV-NOTE:` comment"> | <why it matters in this codebase> |
| <signal — e.g. "Adds new file under `docs/runbooks/`"> | <implication> |
| ... | ... |

## Strong positive signals (title)

Title verbs that map to non-trivial work in this project:

- `<verb>`, `<verb>`, ... — <description of what these usually mean>
- ...

Note any title prefixes that are noisy and require additional confirmation:

- `<verb>` titles are noisy; only treat as positive when paired with another signal.

## Anti-signals (auto-skip before scoring)

Drop the candidate without reading further if any of these are true:

| Anti-signal | Detection |
|---|---|
| <e.g. "Release-flow noise"> | <how to detect — title regex, file glob, etc.> |
| <e.g. "Skill maintenance only"> | <detection> |
| ... | ... |

## High-leverage subsystem paths

A PR that touches any of these paths and isn't an anti-signal is **probably** compound-worthy. Promote it for diff inspection even if the body is thin.

| Path | Why |
|---|---|
| `<path>` | <one-line reason — what makes this subsystem produce subtle bugs / non-obvious patterns> |
| `<path>` | <reason> |
| ... | ... |

## Tempting-but-routine traps

Patterns that look meaty but are usually routine — verify with the diff before promoting:

| Pattern | Why it tempts | Why it's usually routine |
|---|---|---|
| <pattern> | <tempting framing> | <what the diff actually shows> |
| ... | ... | ... |

## Calibration PRs (sanity check set)

A scout calibrated correctly should rediscover most of these as Strong candidates when run over the same window:

- #<number> (<author>) — <one-line synopsis of what made this compound-worthy>
- #<number> (<author>) — <synopsis>
- ... (target: ~10 PRs)

If your scout's strong-candidate set diverges wildly from this list when re-run, your filter is miscalibrated.
```

## Authoring notes

- **Verbatim is the point.** Resist the urge to generalize. `## Why the existing path didn't fire` (specific) outperforms `## Why X didn't work` (paraphrased) because PR bodies are matched by substring.
- **Cite real evidence.** Every signal in this file should be observable in at least 2 of the calibration corpus's 30 days of merged PRs. If you can't cite it, drop it.
- **Update on drift.** When the team adopts a new heading convention or a new high-leverage subsystem appears, edit this file. The calibration workflow can also regenerate it.
- **One file per project.** Do not split this across multiple files. One canonical `.agents/goldpan-signals.md` per repo.
