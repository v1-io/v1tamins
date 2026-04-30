# Quality Gates

## Validation Loop

After completing the report draft:

1. Run `validate_report.py --report [path]`
2. If errors found: fix each one, then re-run validation
3. Max 3 retry cycles. If issues persist after 3 cycles, note them in a comment at the end of the report and move on.

Do not skip validation. Do not proceed to final output without at least one validation pass.

## Anti-Hallucination Protocol

These rules are non-negotiable:

1. **Never fabricate sources.** If you cannot find evidence for a claim, say "No sources found for X" rather than inventing a reference.
2. **Never fabricate URLs.** Every URL in the bibliography must come from an actual WebSearch or WebFetch result.
3. **Never fabricate statistics.** If a number didn't appear in a source, don't include it.
4. **Never fabricate author names.** If the author isn't clear from the source, use the publication/domain name.
5. **Never fabricate dates.** If the publication date isn't available, omit it rather than guessing.
6. **Distinguish fact from synthesis.** When you draw a conclusion that goes beyond what any single source states, flag it: "Based on the convergence of [sources], it appears that..." rather than presenting synthesis as sourced fact.

### Self-Check Before Displaying Output

Before showing the final report to the user:
- Re-read the executive summary. Does every claim trace back to evidence in the body?
- Re-read the bibliography. Does every URL look like a real page you actually visited?
- Check citation numbers. Is every `[N]` in the text matched by an entry `[N]` in the bibliography?

## Anti-Fatigue Protocol

LLMs degrade in quality over long outputs. Guard against this:

### Per-Section Checklist (check after writing EACH section)

- [ ] At least 3 substantive paragraphs
- [ ] Prose-first: bullet points are < 20% of lines
- [ ] No placeholder text ("TBD", "TODO", "to be determined")
- [ ] At least 2 citations per 500 words
- [ ] No repetition of content from previous sections
- [ ] Specific data points, not just generalities

If ANY check fails: regenerate the section before continuing to the next one.

### Late-Section Vigilance

Sections written later in the report are at highest risk of quality degradation. For every section after the third:
- Verify it is at least 80% the length of the average earlier section
- Verify citation density hasn't dropped
- Verify you're introducing new information, not restating earlier sections

## Writing Standards

### Voice and Tone

- Authoritative but not dogmatic
- Direct statements preferred over hedged qualifications
- Active voice default; passive only when the actor is unknown or irrelevant
- No filler phrases: "It is worth noting that", "It should be mentioned that", "Interestingly,"

### Structure Hierarchy

```
# Report Title
## Executive Summary        (standalone, no citations, 200-400 words)
## [Body Section 1]         (evidence-rich, cited)
### [Subsection 1.1]        (if needed for complex sections)
## [Body Section 2]
...
## Limitations               (what this research couldn't answer)
## Methodology               (what was searched, source count, date range)
## Bibliography              (numbered, hyperlinked, matches inline citations)
```

### Comparison Reports

For "X vs Y" queries, the body structure changes:

```
## Executive Summary
## Overview of X
## Overview of Y
## Head-to-Head Comparison    (table format: criteria rows, X/Y columns)
## Analysis                   (detailed breakdown of key differentiators)
## Verdict                    (clear recommendation with reasoning)
## Limitations
## Methodology
## Bibliography
```

The verdict MUST take a position. "It depends on your needs" is not a verdict. State who should choose X, who should choose Y, and why.

## Bibliography Standards

### Format

Each entry:
```
[N] Author/Publication. "Title." Source Domain, Date. URL
```

Example:
```
[1] Smith, J. "The State of AI Code Review in 2026." Nature Machine Intelligence, 2026-01-15. https://nature.com/articles/...
[2] TechCrunch. "Company X Raises $50M for AI-Powered Development Tools." 2025-11-03. https://techcrunch.com/2025/11/03/...
```

### ZERO TOLERANCE

These patterns indicate bibliography truncation. They must NEVER appear:

- `[8-75] Additional references...`
- `[N] ...continue...`
- `[N] etc.`
- `[N] See above`
- `[N] Similar to [M]`
- Any entry covering a RANGE of numbers
- Any entry without a URL

Every inline citation `[N]` in the body MUST have a corresponding `[N]` in the bibliography. No gaps, no ranges.
