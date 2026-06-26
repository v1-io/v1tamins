---
name: v1-html-it
description: Use when creating a self-contained HTML page would help the user understand, compare, review, present, tune, export, or interact with information better than Markdown. Triggers on "make an HTML page", "HTML artifact", "nice HTML", "visual report", "interactive explainer", "one-page dashboard", "shareable page".
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - WebFetch
  - WebSearch
---
# HTML It

Create a self-contained HTML artifact when a visual, spatial, interactive, or easily shareable page will help the user actually inspect and use the work.

## When to Use

Use HTML when the output benefits from at least one of these:

- **Spatial comparison:** alternatives, tradeoffs, diffs, timelines, flowcharts, module maps, or side-by-side options.
- **Visual density:** tables, cards, callouts, color, charts, SVG diagrams, annotated snippets, or status summaries.
- **Quantitative evidence:** charts, dashboards, metric tables, scorecards, small multiples, or visual data reports.
- **Interaction:** tabs, collapsible sections, filters, sliders, toggles, drag/drop, copy buttons, or lightweight editing.
- **Presentation:** a page, deck, explainer, status report, research brief, incident timeline, PR writeup, or review artifact someone else should read.
- **Two-way loop:** the user should manipulate the artifact and export JSON, Markdown, a prompt, a diff, or selected choices back to the agent.

Do not use HTML for:

- One-line answers.
- Simple code patches or command output.
- Durable source docs that should remain clean Markdown.
- Sensitive data that should not be written to disk.
- Artifacts that require a full frontend app, server, authentication, or package install.

## Output Contract

Create one self-contained `.html` file and tell the user where it is.

Default location:

```text
artifacts/html-it/<short-slug>.html
```

If the repo already has an artifact convention, follow it. If the page is temporary or contains private local context, use `/tmp/<short-slug>.html`.

The file must:

- Work by opening directly in a browser.
- Use inline CSS and inline JavaScript.
- Avoid build steps and framework dependencies.
- Use semantic HTML before decorative wrappers.
- Include print-friendly and responsive behavior when useful.
- Include source/provenance notes for reports, reviews, or research.
- Include export/copy controls when the page is interactive or meant to feed a later agent turn.

## Artifact Types

| Need | HTML Shape |
| --- | --- |
| Explore directions | Grid of options with labels, tradeoffs, and selection affordances |
| Compare implementations | Side-by-side panels, callouts, scorecards, and risks |
| Explain code | Module map, annotated snippets, execution path, glossary |
| Review a PR | Annotated diff, severity tags, jump links, reviewer focus areas |
| Product/design review | Component contact sheet, state matrix, design tokens, flow mockups |
| Prototype interaction | Clickable flow, animation sandbox, sliders for timing/easing/values |
| Research/learning | TL;DR, collapsible sections, diagrams, tabs, glossary, FAQ |
| Status/reporting | Timeline, metrics, shipped/slipped/blocked sections, next actions |
| Incident/postmortem | Minute-by-minute timeline, log excerpts, impact bands, follow-ups |
| Custom editing | Purpose-built editor with export/copy as JSON, Markdown, prompt, or diff |

## Workflow

### 1. Choose the Page Job

State the artifact's job in one sentence before building:

```text
This page helps the user [compare/review/understand/tune/present/export] [subject].
```

If the job is vague, pick the closest artifact type from the table. Ask only when the wrong artifact type would waste substantial time.

### 2. Gather the Source Material

Use the available repo, files, conversation, web pages, or command output. Keep a compact evidence list:

- Source files, commits, URLs, screenshots, data exports, or user notes.
- Decisions or questions the page should help answer.
- Audience: the user, reviewers, stakeholders, engineers, operators, or future agents.
- Sensitivity: whether the page can live in the repo or should stay in `/tmp`.

Do not invent data to make the page look complete. Mark unknowns visibly.

If the artifact contains charts, dashboards, metric tables, or quantitative displays, read
[references/visual-evidence-checklist.md](references/visual-evidence-checklist.md) before designing the page.

### 3. Design for Reading First

Make the first viewport useful:

- Put the title, purpose, key takeaway, and primary controls above the fold.
- Use sections, cards, tables, timelines, or diagrams to reduce cognitive load.
- Keep text scannable; avoid long prose blocks.
- Use color to encode meaning, not decoration.
- Keep typography restrained and readable.
- Use whitespace and alignment to reveal structure.
- Prefer real diagrams/charts over ASCII.
- For quantitative displays, make the main comparison, units, filters, source notes, and date range visible near the data.

### 4. Add Interaction Only When It Tightens the Loop

Good interactions:

- Filter or sort dense data.
- Expand details under summaries.
- Switch tabs between alternatives.
- Adjust parameters and see live output.
- Copy selected output back to Markdown, JSON, prompt text, or a diff.

Avoid interaction that is just ornamental. If the page is interactive, include a no-surprise fallback path: visible default state, clear reset, and copy/export result.

### 5. Build the File

Use this skeleton unless the task calls for something more specific:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><!-- concise title --></title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f7f5;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #64707d;
      --line: #d8dde3;
      --accent: #2563eb;
      --good: #0f766e;
      --warn: #b45309;
      --bad: #b91c1c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }
    main { max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    @media print {
      body { background: white; }
      .no-print { display: none !important; }
      .panel { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <main>
    <!-- content -->
  </main>
  <script>
    // Small, local interactions only.
  </script>
</body>
</html>
```

## Quality Bar

Before finishing, check:

- Open the file or verify it is syntactically complete.
- No external network dependency unless explicitly justified.
- No console-breaking JavaScript syntax.
- No overflowing text in buttons, cards, tables, or narrow layouts.
- All interactive controls have labels and obvious state.
- Copy/export buttons produce useful text.
- The artifact states what is sourced, inferred, or missing.
- Quantitative displays pass the visual evidence checklist when applicable.
- Private information is not written into a repo-tracked artifact unless the user explicitly wants that.

## Reference Files

- **[references/visual-evidence-checklist.md](references/visual-evidence-checklist.md)** - Quality checks for charts, dashboards, metric tables, and quantitative visual reports.

## Response Back

Keep the chat response short:

```markdown
Created: [artifact.html](/absolute/path/to/artifact.html)

What it covers:
- ...

Validation:
- Opened locally / checked static HTML / not opened because ...
```

If the artifact is temporary, say so and give the `/tmp` path.
