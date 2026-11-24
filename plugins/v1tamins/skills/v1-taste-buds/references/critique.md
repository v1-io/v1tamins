# Critiquing a design

A critique reports. It changes no files unless the person asks for fixes.

## 1. Get the real thing in view

Work from the rendered result where you can: open the page, the screenshot, the
slide, or the file. When you can only read code, say at the top that the
critique is from code and has not seen the result.

Complete step 1 of the skill first: read what exists, name the case, and name
the surface's job (Decide, Do, or Understand). A critique that ignores the
project's own system produces advice the project cannot use.

## 2. Look in this order

1. **The job.** Can the viewer find the main action or the main takeaway
   within about five seconds? Is anything competing with it?
2. **Hierarchy.** What reads first, second, and third? Is that the right
   order for this audience?
3. **Fit with the system.** Values that bypass tokens, one-off components
   where a shared one exists, and spacing or type that breaks the neighbours'
   pattern.
4. **The floor.** Each line of the floor in the skill: states, sizes,
   contrast, keyboard, motion, type, copy, semantics.
5. **Undecided looks.** Read [defaults.md](defaults.md). Note an entry only
   when neither the brief nor the system explains it.
6. **Copy.** Labels that name the action, consistent names, errors that help.

## 3. Report only what you can point to

A model looking at a screen tends to report faults that are not there. Hold
each finding to this test: you can name the element, state what you observe,
and say how the viewer is affected. Measure what can be measured: compute
contrast from the colour values, read sizes and spacing from the computed
styles. Drop a finding that rests on a general impression.

When the person gives two versions, compare them directly, side by side, and
say which is better on each point. A direct comparison is more reliable than
scoring each alone.

## 4. Output

Use this shape by default and adapt it to the request:

- **Verdict:** one or two sentences. Does the surface do its job, and what is
  the single most valuable change?
- **Findings:** at most seven, ranked by effect on the viewer. For each: where
  it is, what you observe, why it matters to the viewer, and a concrete fix
  with the exact value or token where one applies.
- **Keep:** what works and should survive the next change.
- **Not checked:** anything you could not render, measure, or reach.

Send flow and error-recovery questions to `v1-reviewing-usability`, and chart
integrity questions to `v1-reviewing-data-graphics`. Name the hand-off in the
report; continue with the visual findings that remain yours.
