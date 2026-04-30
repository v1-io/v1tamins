# Report Assembly Strategy

## Progressive Section Generation

Generate the report section-by-section using Write and Edit tools. Never attempt to generate the full report in a single output.

### Word Count Targets

| Mode | Total words | Exec summary | Per section |
|------|------------|--------------|-------------|
| Quick | 2,000-4,000 | 150-250 | 400-800 |
| Standard | 4,000-8,000 | 200-400 | 600-1,500 |
| Deep | 8,000-15,000 | 300-400 | 800-2,000 |

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
2. Write the section (max ~2,000 words per Edit call)
3. Ensure every factual claim has an inline citation `[N]`
4. After writing, update `sources.json` with any new sources cited
5. Verify the section meets anti-fatigue checks before moving on:
   - At least 3 paragraphs
   - Prose-first (< 20% bullet points by line count)
   - No placeholder text
   - At least 2 citations per 500 words

## sources.json Persistence

Create and maintain a `sources.json` file in the output directory. This survives context compaction and enables accurate bibliography generation.

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

These indicate the model is truncating or getting lazy. If you catch yourself writing any of these, STOP and regenerate the section:

- "Content continues..."
- "Due to length constraints..."
- "[Sections X-Y follow similar analysis]"
- "As discussed above..." (without adding new information)
- "And many more..."
- "etc." at the end of a substantive list
- "[Additional citations omitted]"
- "[8-75] Further references..."
- Any bibliography entry that covers a RANGE of citation numbers
