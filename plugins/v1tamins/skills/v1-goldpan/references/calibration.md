# Calibration Workflow

Calibration grounds this skill in the team's actual writing style by analyzing recent merged PRs and producing `.agents/goldpan-signals.md` — a project-specific evidence file that future scout runs use to score candidates.

Run on first use, or with `/v1-goldpan recalibrate` to refresh after major team or codebase changes (new authors joined, large refactors, framework migrations).

## When this runs

- Phase 0 of the goldpan workflow detects no `.agents/goldpan-signals.md` and the user opts in via the blocking question.
- The user passes `recalibrate` as the skill argument explicitly.

Calibration is not free (~3-5 min, dispatches 4 parallel research agents). Do not auto-run silently.

## Inputs

- The current project's last 30 days of merged PRs to the configured base branch (default `main`)
- The compound-worthiness rubric in [scoring.md](scoring.md)
- The empty template in [pr-signals-template.md](pr-signals-template.md)

## Workflow

### Step 1: Size the corpus

```bash
BASE_BRANCH="main"   # override from .agents/goldpan.config.yaml if present
SINCE=$(python3 -c "import datetime; print((datetime.date.today() - datetime.timedelta(days=30)).isoformat())")

gh pr list --state merged --base "$BASE_BRANCH" \
  --search "merged:>=$SINCE" \
  --json number,title,author,mergedAt \
  --limit 200 \
| python3 -c "
import json, sys
from collections import Counter
prs = json.load(sys.stdin)
print(f'Total: {len(prs)}')
authors = Counter(p['author']['login'] for p in prs)
print('Top authors:')
for a, c in authors.most_common(8):
    pct = 100 * c / len(prs)
    print(f'  {a}: {c} ({pct:.0f}%)')
"
```

If the corpus is <20 PRs, calibration evidence will be thin. Tell the user and offer to widen the window to 60 or 90 days, or to skip calibration entirely.

### Step 2: Dispatch parallel research agents

Launch four `general-purpose` Agents **in parallel**. Each agent gets the rubric ([scoring.md](scoring.md)) and a focused brief. Caps each response at ~600-1000 words.

**Agent 1 — Top-author cohort**: characterize PR style of the highest-volume author. If that author is an automated bot, this matters most because most of the corpus comes from it.

**Agent 2 — Second-highest author cohort**: same brief, second author.

**Agent 3 — Human-author cohort** (if humans contribute and aren't already covered): the human PRs are usually the highest-signal candidates because humans tend to write proper rationale. If all three top authors are bots, replace this with a third bot cohort.

**Agent 4 — Cross-cutting compound-worthy hunt**: scan the full corpus, shortlist ~10 strong candidates by reading both bodies AND diffs, characterize what compound-worthy looks like in *this* codebase (high-leverage subsystems, file-path patterns, body shapes, anti-patterns).

### Per-agent prompt template

```
You are doing research for an agent skill that scans PRs to find candidates
for /ce-compound documentation. Help me ground the skill's PR scout in
reality rather than assumed language.

Context: this repo merges ~<N> PRs/month. The author <X> accounts for ~<Y>%
of PRs. I need to understand its PR style so the scout can effectively
distinguish compound-worthy work from routine work in this author's output.

Task: pick a stratified sample of 20 PRs by <X> merged to <base-branch> in
the last 30 days (mix of titles that look small/medium/large). For each PR:
- gh pr view <num> --json number,title,body,commits,files
- Note: body section headings, presence of any "Problem/Why/Root cause/What
  didn't work" framing, commit message style, and the type of changes (file
  paths, languages, bug fix vs feature vs config tweak).
- Spot-check 2-3 PRs with gh pr diff <num> to see whether body claims match
  the diff.

Synthesize and return:
1. Body shape — what sections actually appear, are they templated, do they
   contain real rationale?
2. Title patterns — how do "fix subtle bug" titles look vs "refactor X" vs
   "add feature"?
3. Compound-worthiness distribution — out of 20, how many would be worth
   /ce-compound? Why (or why not)?
4. Real signals that distinguish a compound-worthy <X> PR from a routine
   one (be specific — actual phrases observed verbatim, not assumed ones).
5. Anti-signals — phrases or patterns that mean "skip this".
6. Diff-level signals — what does the diff itself reveal that the body
   doesn't?

Important: do not invent generic phrases. Quote what ACTUALLY appears.
Cite specific PR numbers throughout. Cap response at ~600 words.

Working directory: <project-cwd>
```

For Agent 4 (cross-cutting), brief:

```
Find genuinely compound-worthy PRs in the last 30 days of merges to
<base-branch>, by reading actual diffs.

Task:
1. List all merged PRs from the last 30 days.
2. Use title + author to shortlist ~30 PR numbers most likely to be
   compound-worthy. Bias toward titles with "fix", "harden", "prevent",
   that mention specific bugs/subsystems. Avoid "feat: Add X", "Update
   dependencies", "Bump version", workflow-only tweaks.
3. For each shortlisted PR run gh pr view AND gh pr diff <num> | head -300.
   Read both.
4. Score each as: Strong / Maybe / No with one-sentence reason citing
   specific evidence from body OR diff.

Synthesize:
1. Strong candidates list (~5-10 PR numbers) with title, one-paragraph
   synopsis of what makes it compound-worthy, suggested category, verbatim
   evidence.
2. What "compound-worthy" actually looks like in THIS repo — patterns
   common to your strong candidates that a scout could match on. Be
   concrete: file path patterns, phrase patterns, diff shapes.
3. What looks compound-worthy but isn't — examples of titles/bodies that
   would tempt a scout but where the diff reveals routine work.
4. Diff-shape heuristics — files changed, lines changed, presence of
   tests/migrations/runbooks.
5. Per-subsystem patterns — what does compound-worthy work look like in
   each high-leverage subsystem you identify?

Cap at ~1000 words. Quote actual content. Cite PR numbers throughout.
```

### Step 3: Synthesize the signals file

Once all four agents return, merge their findings into `.agents/goldpan-signals.md` using [pr-signals-template.md](pr-signals-template.md) as the structure. Specifically:

- **Author cohorts table**: from Agents 1-3, with share %, compound rate, and bias note.
- **Strong positive signals (body)**: union of verbatim section headings and phrases all four agents observed. Drop anything that appeared <2 times across agents (probably noise).
- **Strong positive signals (diff)**: union of diff-level tells (added marker comments, runbooks added, structural tests, telemetry fields, etc.).
- **Strong positive signals (title)**: title verbs that map to non-trivial work, with frequency notes.
- **Anti-signals**: file-path globs, title prefixes, body shapes that consistently produce routine work.
- **High-leverage subsystem paths**: from Agent 4's per-subsystem section.
- **Tempting-but-routine traps**: from Agent 4's "looks compound-worthy but isn't".
- **Calibration PR set**: Agent 4's strong candidates list (~10 PR numbers with one-line summaries) — used as a sanity check by future scouts.

Do not paraphrase or generalize the signals. The point of calibration is to capture **verbatim** what this team writes.

### Step 4: Show and confirm

After writing `.agents/goldpan-signals.md`:

1. Print a 5-line summary: total PRs analyzed, number of strong candidates found, top 3 verbatim signals discovered, top 3 anti-signals.
2. Ask the user to skim the file and confirm before the goldpan scouts use it.
3. Note that the file is editable — users can add/remove signals manually.

### Step 5: Proceed to panning

Once confirmed, continue to Phase 1 of the goldpan workflow with the new signals file in scope.

## Maintenance

The signals file becomes stale when:
- A major bot author is replaced or retires
- The team adopts a new convention (new section heading like `## Failure Mode`)
- A large refactor changes which subsystems are "high-leverage"
- The codebase moves to a new language/framework

Trigger a fresh calibration with `/v1-goldpan recalibrate`. The previous signals file is overwritten — git history preserves it if the file is committed.

## When calibration should be skipped

- Project has <20 merged PRs total — too little corpus, fall back to universal signals
- Calibration was just run within the last 30 days — re-running is wasteful
- The user explicitly opts out via the Phase 0 blocking question
