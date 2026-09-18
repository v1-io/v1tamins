# Research Methodology

Work in three phases: PLAN, RESEARCH, then SYNTHESIZE. Don't skip any. Each
phase builds on the last.

---

## Phase 1: PLAN

### 1.1 Classify the Query

Name the query type. It shapes how you search and how you write the report.

| Type | Signal | Search bias | Output bias |
|------|--------|-------------|-------------|
| ANALYSIS | "analyze", "evaluate", "assess" | Academic + industry sources | Evidence-weighted argument |
| COMPARISON | "vs", "compare", "difference between" | Parallel research per subject | Side-by-side with verdict |
| HOW_TO | "how to", "best practices", "guide" | Tutorials, docs, Stack Overflow | Step-by-step with rationale |
| NEWS | "latest", "recent", "what happened" | News sites, date-filtered | Timeline + implications |
| EXPLORATORY | Default / open-ended | Broad mix | Landscape overview |

Store the classification: `QUERY_TYPE = [type]`

### 1.2 Orientation Searches

Run 2-3 broad WebSearch queries before you lock the sub-queries. Use the
current date from Step 0.

```
WebSearch("[topic] overview 2026")
WebSearch("[topic] recent developments")
```

Scan results for: key terminology, major players, controversies, recent events.
Use those to generate sub-queries.

### 1.3 Generate Sub-Queries

Split the research question into independent search angles. Each sub-query
should hit a different facet:

| Angle | Example for "AI code review tools" |
|-------|-------------------------------------|
| Core landscape | "AI code review tools comparison 2026" |
| Technical depth | "static analysis vs LLM code review accuracy benchmarks" |
| Recent developments | "AI code review tools launched 2025 2026" |
| Academic/research | "automated code review machine learning research papers" |
| Critical/contrarian | "AI code review limitations problems criticism" |
| Quantitative | "AI code review tool adoption statistics developer survey" |
| Industry perspective | "enterprise AI code review ROI case study" |

Generate the number of sub-queries the mode specifies (3/5/7). Every sub-query
must be distinct -- no overlapping angles.

### 1.4 Draft Initial Outline

From the orientation results and sub-queries, draft a section outline. It's
provisional. Phase 3 may restructure it from the evidence.

---

## Phase 2: RESEARCH

### 2.1 Parallel Sub-Query Execution

Fire all sub-queries in one message as parallel WebSearch calls.

```
# In a SINGLE message, fire all sub-queries:
WebSearch("AI code review tools comparison 2026")
WebSearch("static analysis vs LLM code review accuracy benchmarks")
WebSearch("AI code review tools launched 2025 2026")
...
```

For each search result that looks substantive, fetch the full page:
```
WebFetch(url, "Extract key facts, data, and claims about [topic]. Include specific numbers, dates, and named entities.")
```

### 2.2 Sub-Agent Deep Dives (Standard + Deep modes)

Spawn sub-agents for angles that need a deeper look. Give each a focused brief.
They return structured evidence:

```
Agent(
  description="Research [specific angle]",
  prompt="Research [specific angle] for [topic]. Return findings as a JSON array:
    [{
      \"claim\": \"specific factual claim\",
      \"evidence\": \"direct quote or data point\",
      \"source_url\": \"https://...\",
      \"source_title\": \"...\",
      \"confidence\": \"high|medium|low\"
    }]
    Use WebSearch and WebFetch. Find 5+ sources. Prioritize quantitative data."
)
```

Sub-agents run in parallel. Standard mode: 2 agents. Deep mode: 3 agents.

### 2.3 Learning Extraction

After searches and sub-agents finish, pull the learnings into a structured list:

1. List every distinct claim with its source(s)
2. Flag claims with only 1 source as "unverified"
3. Flag contradictions between sources -- document both sides
4. Assign confidence: HIGH (3+ independent sources), MEDIUM (2 sources), LOW (1 source)
5. Note which claims have quantitative backing vs. qualitative only

Write learnings to `sources.json` in the output directory (see report-assembly.md).

### 2.4 Gap Identification and Follow-Up

Review the learnings against the outline. Find:
- Sections with thin evidence (< 2 sources)
- Unanswered sub-questions from the original query
- Contradictions that need resolution
- Missing quantitative data where qualitative claims exist

Run targeted follow-up searches on the gaps. Use HALF the breadth of the
original search round:
- Standard mode: 2-3 follow-up searches
- Deep mode: 3-5 follow-up searches, can run 2 rounds

Point each follow-up search at one specific gap.

### 2.5 Source Curation (Deep mode only)

Review all collected sources. For each, assess:
- Domain authority (academic > gov > established media > blog)
- Recency (prefer last 12 months unless historical context needed)
- Specificity (concrete data > general commentary)
- Potential bias (vendor whitepapers, sponsored content)

Drop sources scoring poorly on 3+ criteria. Flag remaining biased sources for
disclosure in the report.

---

## Phase 3: SYNTHESIZE

### 3.1 Outline Refinement

Compare the initial outline (from 1.4) against the evidence you actually
collected. Restructure if:
- Evidence reveals a more important angle than originally planned
- A planned section has insufficient evidence (merge or drop)
- An unexpected theme emerged across multiple sources

Constraints:
- Max 50% restructuring from original outline
- Every restructuring decision must be evidence-driven
- Preserve the user's original question as the through-line

### 3.2 Report Generation

Follow `reference/report-assembly.md` for section-by-section writing.

Key rules:
- Write each section individually using Write/Edit tools
- Max ~2,000 words per tool call
- Every factual claim needs an inline citation `[N]`
- Maintain `sources.json` on disk as you write

### 3.3 Critique (Standard + Deep modes)

After the first draft is complete, run a critique pass.

**Standard mode -- Single-pass critique:**
Review the report for: unsupported claims, logical gaps, missing
counterarguments, hedging language, vague conclusions. Fix inline.

**Deep mode -- Three-angle critique:**
Check the draft from three angles:
1. Would someone working in this field trust these findings? What's missing
   for a practitioner?
2. What claims are weakest? Where is the evidence thin? What other
   explanations exist?
3. Can someone act on these conclusions? Are the recommendations specific
   enough?

For each angle, write 3-5 critique points. Address each one:
- If it's a writing issue: fix inline
- If it's a knowledge gap: run delta-queries (max 2-3 targeted searches,
  time-boxed to 3 minutes)

### 3.4 Validation

Run the validation script:
```bash
python3 [skill-root]/scripts/validate_report.py --report [path]
```

Fix any errors. Re-run validation. Max 3 retry cycles, then stop and note
remaining issues.

### 3.5 Final Output

1. Ensure all bibliography entries are numbered and match inline citations
2. Add methodology note (sources searched, date range, mode used)
3. Save to `~/Documents/Research/[Topic]_[YYYYMMDD]/report.md`
4. Display executive summary to user with source count and word count

---

## Comparison Mode

Triggered by "X vs Y", "compare", "difference between" queries.

1. Run THREE parallel research passes using sub-agents:
   - Agent 1: Research subject A independently
   - Agent 2: Research subject B independently
   - Agent 3: Research "A vs B" direct comparisons

2. Synthesize into a structured comparison:
   - Overview of each subject
   - Head-to-head comparison table (criteria as rows, subjects as columns)
   - Strengths / weaknesses for each
   - Verdict with reasoning (take a position -- "it depends on your needs"
     is not a verdict)

---

## Context Mode (`--context`)

When invoked with `--context`, skip the full report. Instead:

1. Run PLAN and RESEARCH phases as normal
2. Output a compact summary (500-1000 words):
   - Key findings (bulleted, with source URLs)
   - Confidence assessment
   - Open questions
3. Format for consumption by other skills or follow-up conversations
