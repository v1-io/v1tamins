---
name: v1-canon2skill
description: Use when turning a textbook, PDF, blog post, article, paper, course, notes, transcript, or other source material into suggested agent skills or skill improvements. Triggers on "what skills could come from this", "extract skills from", "turn this into skills", "skill ideas from this source".
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - WebFetch
  - WebSearch
---
# Canon2skill

Turn large source material into evidence-backed recommendations for new or improved agent skills.

## Output Contract

Produce recommendations, not final skill files, unless the user explicitly asks to build them.

Default output:

```markdown
## Recommended Skills

| Rank | Skill | Placement | Why It Exists | Evidence Coverage | Build Shape |
| --- | --- | --- | --- | --- | --- |

## Best First Skill
[One recommendation with trigger, core workflow, likely files, and validation approach.]

## Coverage Matrix

| Source Area | Covered By | Evidence | Gaps |
| --- | --- | --- | --- |

## Do Not Build
[Useful ideas that are too factual, narrow, generic, private, or not procedural enough.]

## Data Gaps
[Extraction failures, missing figures/tables, OCR uncertainty, inaccessible pages, or source limits.]
```

Include concise citations to source sections, page numbers, URLs, headings, timestamps, or chunk ids wherever possible.

## Workflow

### 1. Ingest the Source

Identify the source type and preserve provenance before summarizing.

| Input | Ingestion |
| --- | --- |
| URL or blog post | Fetch the page, preserve URL, title, headings, and publication date if visible. |
| Plain text or Markdown | Save or reference the text with heading boundaries intact. |
| Born-digital PDF | Extract text with page numbers. Prefer structured Markdown extraction when available. |
| Scanned PDF | Run OCR first if local tools are available; otherwise flag OCR as a data gap. |
| Slides or images | Extract speaker notes/text where possible and flag visual-only material as a gap unless image understanding is available. |

For PDFs, try available local tools in this order and record what worked:

```bash
command -v pymupdf4llm || true
command -v python3 || true
command -v pdftotext || true
command -v ocrmypdf || true
command -v tesseract || true
command -v swift || true
```

Use deterministic extraction first. Use the model to repair structure, headings, and noisy OCR only after extraction.

### PDF OCR Fallback

Always verify extraction quality before summarizing:

```bash
pdftotext -layout -enc UTF-8 input.pdf extracted.txt
wc -w extracted.txt
```

If the extracted text has near-zero words, mostly page breaks, or obviously missing chapters, treat the PDF as scanned/image-only even if `pdfinfo` reports normal pages.

OCR fallback order:

1. If `ocrmypdf` is available, create a searchable copy, then run text extraction again.
2. If `tesseract` plus PDF image rendering tools are available, render pages and OCR them with page markers.
3. On macOS with `swift` available, use the bundled Vision OCR helper:
   ```bash
   swift "$SKILL_DIR/scripts/ocr-pdf-macos.swift" input.pdf ocr.txt
   ```
   If the host does not expose `SKILL_DIR`, resolve `scripts/ocr-pdf-macos.swift` relative to this skill directory.
4. If OCR is not possible locally, report the blocker as a data gap and do not pretend the source was read.

For OCR output, preserve page markers such as `=== Page 12 ===`. Treat OCR as lower-confidence than embedded text and spot-check early, middle, and late pages before using it for recommendations.

### 2. Build a Source Map

Create a compact inventory before interpreting the material:

- Document metadata: title, author/source, date if available, input path or URL.
- Structure: chapters, sections, headings, page ranges, or timestamps.
- Extraction quality: clean, partial, OCR-heavy, table-heavy, image-heavy, or blocked.
- Provenance scheme: page numbers, section ids, chunk ids, or URL anchors.

For long sources, chunk by semantic boundaries before token size:

1. Preserve chapter and heading hierarchy.
2. Keep tables, examples, exercises, and checklists attached to the nearest heading.
3. Use overlapping chunks only when a concept crosses boundaries.
4. Assign stable ids such as `ch03-sec02-p45-52`.

### 3. Create Learning Cards

For each chunk, extract a short learning card:

```markdown
### [chunk id]
- Core concepts:
- Procedures or workflows:
- Decision rules:
- Failure modes:
- Examples or exercises:
- Terms of art:
- Possible agent behavior:
- Evidence:
```

Do not compress directly into skill ideas yet. First gather the reusable behaviors the source teaches.

### 4. Roll Up Concepts Recursively

Summarize upward in layers:

1. Chunk cards -> section summaries.
2. Section summaries -> chapter or article-part summaries.
3. Chapter summaries -> source-level concept map.

At each layer, keep:

- Concepts that recur across sections.
- Procedures with ordered steps.
- Decisions with explicit tradeoffs.
- Failure modes with prevention or diagnosis steps.
- Examples that reveal tacit judgment.
- Contradictions, caveats, or scope boundaries.

Keep the rollup lossy enough to fit in context, but never drop provenance ids.

### 5. Generate Candidate Skills

Convert concepts into candidate skills only when they imply reusable agent behavior.

Score each candidate from 1-5:

| Criterion | Question |
| --- | --- |
| Reusable | Would this help across multiple future tasks? |
| Procedural | Does it teach a workflow, decision rule, checklist, or validation loop? |
| Non-obvious | Would a general model likely miss or mishandle this without guidance? |
| Testable | Can success be evaluated on realistic examples? |
| Bounded | Is it narrow enough to fit one skill without becoming a course summary? |
| Public-safe | Can it be written without private names, URLs, secrets, customer facts, or project-only context? |

Prefer skill improvements over new skills when the material deepens an existing workflow. Inspect existing skill names and descriptions when working in a skill repository.

### 6. Re-read Against the Full Source

For every promising candidate:

1. Turn the candidate into explicit claims: "this skill should teach X."
2. Retrieve or re-open all chunks relevant to each claim.
3. Check both false positives and false negatives:
   - False positive: the skill claims something the source does not support.
   - False negative: the source teaches an important behavior missing from the skill.
4. Build a coverage matrix with source areas, candidate skill components, evidence, and gaps.
5. Demote candidates that are mostly facts, summaries, motivation, or generic advice.

This re-read step is mandatory for large sources. Do not trust the first rollup alone.

### 7. Apply the Skill-Worthiness Gate

Recommend a skill only if it passes at least one gate:

- The source contains a repeatable workflow agents can follow.
- The source contains decision rules that improve task routing or tradeoffs.
- The source contains failure modes that can become validation checks.
- The source contains examples that can become evaluation cases.
- The source reveals a missing capability in existing skills.

Do not recommend a skill for:

- A concept glossary without agent behavior.
- A generic best-practices list the model already knows.
- A one-off project procedure.
- Material that cannot be made public-safe.
- Content that would be better as a reference file inside an existing skill.

## Existing Skill Repositories

When running inside a skill repository:

1. Inspect current skills before proposing new ones:
   ```bash
   find . -maxdepth 5 -path '*/SKILL.md' -print
   ```
2. Separate recommendations into:
   - New shared skill.
   - Improvement to existing skill.
   - Private/project-local instruction.
   - Do not build.
3. For public repositories, include a privacy rationale for each recommendation.

## Naming Guidance

Suggest short gerund-form names:

- `canon2skill`
- `reviewing-documents`
- `debugging-traces`

Avoid vague nouns such as `assistant`, `helper`, `toolkit`, `playbook`, or `knowledge`.

## Validation Prompts

Use these checks before finalizing recommendations:

```text
Which recommendations are just summaries rather than reusable agent workflows?
```

```text
What important source lessons are missing from the proposed skills?
```

```text
Which recommendations should be improvements to existing skills instead of new skills?
```

```text
What source areas were weakly extracted or not inspected?
```

## Source Handling Rules

- Preserve page, section, URL, or chunk provenance from ingestion through final output.
- Prefer structured extraction over ad hoc prose scanning.
- Verify PDF extraction quality; image-only PDFs require OCR before learning-card generation.
- Treat tables, diagrams, exercises, and examples as high-value skill evidence.
- Mark uncertainty when extraction quality is low.
- Do not include copyrighted long excerpts in the final output; cite and paraphrase instead.
- Do not leak private source details when recommending public shared skills.
