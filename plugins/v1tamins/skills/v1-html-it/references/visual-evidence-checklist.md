# Visual Evidence Checklist

Use this reference when an HTML artifact contains charts, dashboards, quantitative displays, metric tables, or visual evidence.

## Table Of Contents

- [First Viewport](#first-viewport)
- [Integrity](#integrity)
- [Comparison](#comparison)
- [Data-Ink And Apparatus](#data-ink-and-apparatus)
- [Density And Small Multiples](#density-and-small-multiples)
- [Labels, Legends, And Text](#labels-legends-and-text)
- [Interaction](#interaction)
- [Validation](#validation)

## First Viewport

Make the first viewport answer the artifact's job.

- Put the main claim, current filter/window, and primary comparison above the fold.
- Show the actual data view early, not a decorative hero or explanatory preamble.
- Keep enough of the next section visible that the page invites inspection.
- Use visual hierarchy to separate the claim, data, caveats, and controls.

## Integrity

Quantitative displays must not visually overstate or understate the data.

- Match visual magnitude to data magnitude. Avoid using area, volume, perspective, or icon size for a one-dimensional value unless that encoding is clearly intentional and tested.
- Do not truncate an axis when the mark length implies magnitude unless the break is explicit and defensible.
- Include units, denominators, date ranges, source notes, and active filters near the display.
- Use real-vs-nominal, rate-vs-count, and absolute-vs-relative views intentionally. Label which one is shown.
- Show uncertainty, missing data, or partial periods when those facts affect interpretation.
- If the graphic makes a claim, include the comparison needed to evaluate that claim.

## Comparison

Design around the comparison the viewer must make.

- Align comparable quantities on a shared baseline when possible.
- Put peer groups, prior periods, targets, or thresholds close to the data they explain.
- Use annotations for events that explain regime changes, outliers, or discontinuities.
- Prefer sorted or grouped layouts when ranking matters.
- Prefer consistent scales across small multiples unless differing scales are explicitly labeled and necessary.

## Data-Ink And Apparatus

Every visible mark should earn its place.

- Keep data marks and direct annotations visually stronger than frames, grids, axes, and container chrome.
- Use light reference marks; heavy grids and borders should be rare.
- Remove duplicate labels, repeated legends, decorative icons, shadows, fake perspective, and background texture when they do not carry information.
- Keep orientation marks that help reading. Do not erase useful scale, grouping, or context for the sake of visual minimalism.
- Use color to encode meaning or state, not to make a sparse chart look richer.

## Density And Small Multiples

Dense is good when it increases understanding per unit of attention.

- Preserve density when the viewer can scan clear rows, columns, facets, or repeated forms.
- Use small multiples for repeated comparisons over a changing index variable such as time, segment, region, scenario, or cohort.
- Prefer one well-structured dense view over many sparse cards when the task is comparison.
- Split or simplify when density becomes a decoding puzzle, especially when users must constantly consult a legend.
- Keep repeated scales, labels, and spacing stable so differences belong to the data, not the layout.

## Labels, Legends, And Text

Words, numbers, and graphics should work as one display.

- Prefer direct labels near the relevant marks when practical.
- Keep labels horizontal or otherwise easy to read.
- Use legends only when direct labels would clutter the display more than they help.
- Treat charts as paragraphs about data: integrate them with nearby explanatory text rather than isolating them far from the claim.
- Put exact values in labels, tooltips, or tables when decisions require precision.
- Spell out unfamiliar encodings and avoid mysterious abbreviations.

## Interaction

Interaction should tighten inspection, not decorate the page.

- Make default filters visible.
- Keep hover-only information available through labels, tables, or keyboard-accessible controls when it is essential.
- Provide reset controls when filters, toggles, or sliders can materially change the conclusion.
- Avoid animation that changes scale, order, or framing in ways that obscure comparison.
- If users can export or copy the artifact, include the active filters and source notes in the exported text.

## Validation

Before finishing a chart-heavy HTML artifact:

- Inspect the rendered page at desktop and mobile sizes.
- Check that labels do not overlap at the smallest supported width.
- Verify that colors remain distinguishable without relying on hue alone.
- Compare the rendered numbers against the source data or command output.
- Ask what a rushed viewer would conclude, then verify that conclusion is supported by the data.
- State any missing data, inaccessible source, or unverified assumption in the artifact.
