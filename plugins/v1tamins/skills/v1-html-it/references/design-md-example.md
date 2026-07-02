# Design.md Example

Use this reference when an HTML artifact should follow a durable visual system instead of one-off styling.

This is a public-safe synthetic example. It is not extracted from a real brand, customer, product, or private project.

## Pattern

Treat the files as separate inputs with separate jobs:

- `design.md` is the reusable visual recipe: type, spacing, colors, interaction tone, and forbidden moves.
- The skill prompt is the current artifact job: audience, content, states, and verification.
- The generated HTML is the finished artifact: it should obey both inputs without copying unrelated examples.

## Tiny `design.md`

```markdown
# Design System: Focused Console

## Product Context

Create utilitarian internal tools for repeat operators. The interface should feel calm, dense, and trustworthy, not promotional.

## Visual Principles

- Lead with the user's current decision or next action.
- Prefer aligned lists, tables, segmented controls, and compact panels over large marketing sections.
- Use color to encode state or priority. Do not use decorative gradients, floating blobs, or ornamental illustrations.
- Keep repeated items visually consistent so users can scan differences quickly.

## Type

- System font stack.
- Body text: 14-16px.
- Section headings: 16-20px, medium weight.
- Avoid viewport-scaled text and negative letter spacing.

## Color Tokens

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#f6f5f2` | Page background |
| `--surface` | `#ffffff` | Tool panels and repeated cards |
| `--ink` | `#20242a` | Primary text |
| `--muted` | `#69717d` | Secondary text |
| `--line` | `#d8d4ca` | Borders and dividers |
| `--accent` | `#2563eb` | Primary action and selected state |
| `--good` | `#0f766e` | Healthy or complete state |
| `--warn` | `#b45309` | Needs attention |
| `--bad` | `#b91c1c` | Failing or blocked state |

## Layout

- Constrain main content to `1120px`.
- Use `8px` border radius for cards, panels, buttons, and inputs.
- Use a 4px spacing base: `4, 8, 12, 16, 24, 32`.
- Keep the first viewport useful: title, current status, primary controls, and at least one real content row should be visible.

## Components

- Buttons: icon or short verb first, stable height, visible focus state.
- Cards: only for repeated items or framed tools. Do not put cards inside cards.
- Tables: use when comparison matters. Keep column headers visible and labels plain.
- Empty states: name what is missing and expose the next action.

## Interaction

- Every control needs a visible default state.
- Filters must include a reset path.
- Copy/export actions should include source notes and active filters.
- Motion should be functional and subtle; avoid decorative animation.
```

## Paired Skill Prompt

```text
/v1-html-it create a self-contained HTML artifact for a project status console.

Use the attached design.md as the visual recipe. Build one file that opens directly in a browser.

Artifact job:
- Help an operator compare five active workstreams and decide what needs attention.
- Include status, owner placeholder, last checked time placeholder, risk, next action, and evidence note for each workstream.
- Include filters for status and a copy button that exports a Markdown handoff.

Constraints:
- Use synthetic placeholder content only.
- Keep the page dense and scannable.
- Do not create a landing page or marketing hero.
- Do not use external assets, external scripts, or network calls.

Validation:
- Check desktop and narrow mobile layout.
- Verify the copy/export output includes active filters and source notes.
- State that the data is synthetic in the artifact.
```

## Verification Checklist

- Confirm the generated page visibly uses the `design.md` tokens and layout rules.
- Check that no private names, paths, URLs, tickets, account IDs, or secrets entered the artifact.
- Verify the artifact's controls and copy/export output still serve the artifact job.
- Remove design rules that the output ignored; add only rules that change observable behavior.
