# Report Assembly

## Progressive Section Generation

Write the report one section at a time with Write and Edit. Don't try to dump
the whole report in one go.

### Length

Length follows evidence: Quick answers the question; Standard and Deep cover every sub-question with cited evidence.

### Generation Order

1. Create the output directory: `~/Documents/Research/[Topic]_[YYYYMMDD]/`
2. Initialize `sources.json` (see below)
3. Write the report skeleton (title, section headers, bibliography placeholder)
4. Generate each body section sequentially, updating `sources.json` after each
5. Write the executive summary LAST (it summarizes the full report)
6. Generate the bibliography from `sources.json`

### Per-Section Protocol

For each section:
1. Review the evidence collected for this section from Phase 2 learnings
2. Write the section
3. Ensure every factual claim has an inline citation `[N]`
4. After writing, update `sources.json` with any new sources cited
5. Verify the section meets anti-fatigue checks before moving on:
   - At least 3 paragraphs
   - Prose-first (< 20% bullet points by line count)
   - No placeholder text
   - At least 2 citations per 500 words

## sources.json Persistence

Create and keep a `sources.json` file in the output directory. It survives
context compaction and is what you build the bibliography from.

```json
{
  "metadata": {
    "topic": "...",
    "mode": "standard",
    "date": "2026-03-26",
    "query_type": "ANALYSIS"
  },
  "sources": [
    {
      "id": 1,
      "url": "https://...",
      "title": "...",
      "author": "...",
      "date": "2026-01-15",
      "domain": "nature.com",
      "cited_in_sections": ["Introduction", "Technical Analysis"],
      "key_claims": ["claim supported by this source"]
    }
  ],
  "citation_counter": 1
}
```

Update after each section:
```python
# Read current state
sources = json.load(open("sources.json"))
# Add new source
sources["citation_counter"] += 1
sources["sources"].append({...})
# Write back
json.dump(sources, open("sources.json", "w"), indent=2)
```

## Section Writing Standards

### Prose-First

Default to flowing prose paragraphs. Use bullet points ONLY for:
- Lists of 4+ parallel items (tools, features, steps)
- Comparison criteria
- Recommendations / action items

BAD:
```
* The market grew 15% in 2025
* Key players include Company A and Company B
* Adoption barriers remain significant
```

GOOD:
```
The market grew 15% in 2025, driven primarily by enterprise adoption in
the financial services and healthcare sectors [3]. Company A and Company B
emerged as market leaders, collectively capturing 40% of revenue [4][7].
Despite this growth, significant adoption barriers remain -- particularly
around data privacy concerns and integration complexity with legacy
systems [5].
```

### Precision Over Hedging

BAD: "AI has significantly improved outcomes in various domains."
GOOD: "GPT-4 reduced diagnostic error rates by 23% across 14 radiology departments (n=12,400 cases, p<0.01) [8]."

BAD: "Many experts believe this trend will continue."
GOOD: "Seven of nine surveyed analysts project 15-25% annual growth through 2028 [12], though two cite regulatory headwinds that could slow adoption to single digits [13]."

### Citation Density

Target: 2-4 citations per 500 words for body sections. The executive summary has zero citations (it's a standalone summary). The methodology note has zero citations.

### FORBIDDEN Patterns

These mean you cut the section short. If you write any of these, stop and
rewrite the section:

- "Content continues..."
- "Due to length constraints..."
- "[Sections X-Y follow similar analysis]"
- "As discussed above..." (without adding new information)
- "And many more..."
- "etc." at the end of a substantive list
- "[Additional citations omitted]"
- "[8-75] Further references..."
- Any bibliography entry that covers a RANGE of citation numbers
