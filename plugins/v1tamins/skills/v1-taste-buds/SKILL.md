---
name: v1-taste-buds
description: Use when designing, building, or critiquing frontend UI, pages, components, slides, or diagrams. Triggers on "design this", "make it look better", or "critique this design".
---

# Taste Buds

Design and refine what people see and use: pages, app screens, components,
standalone HTML, slides, diagrams, and graphics. The person supplies the taste.
This workflow supplies the process, the options to choose from, and the floor.

Three rules outrank everything below:

1. **What exists wins.** An existing design system, a brand, or the brief's own
   words override every default and preference in this skill.
2. **The person picks the look.** When the look is open, run a tasting and let
   them choose.
3. **Judge the rendered result.** Look at what was built, at the sizes it ships
   at, before you call it done.

## Choose the workflow

- **Build or change a visual surface:** follow steps 1 to 6.
- **Critique without editing:** read [critique.md](references/critique.md) and
  follow it in place of steps 2 to 6.
- **Slides, diagrams, graphics, or documents:** read
  [other-media.md](references/other-media.md) after step 1. It adapts the
  tasting, the floor, and the viewing sizes to each medium.

Hand off when another skill owns the question:

- `v1-reviewing-usability` when the question is whether a user can complete a
  flow and recover from mistakes.
- `v1-reviewing-data-graphics` when a chart or dashboard may mislead.
- `v1-html-it` owns the job, structure, and delivery of a standalone HTML
  artifact, and `v1-explainer-video` owns narrated animation. Supply their
  visual decisions from this skill; they keep the overall result.
- `v1-prove-work` to record finished browser behavior as evidence.

Native iOS and Android platform conventions are outside this skill. Apply the
floor to such screens and say that platform guidance was not applied.

## 1. Read what exists

Before any visual decision, read the project's visual truth: a `DESIGN.md` or
other design document, token and theme files, the component library, brand
assets, and two or three neighbouring screens or slides. Then name the case.

| Case | Evidence | What you do |
| --- | --- | --- |
| **Existing system** | Tokens, components, or a design document | Build with its components and tokens. Add a new colour, font, radius, or spacing value only as a new token, and say that you added it. |
| **Undocumented look** | Consistent styling in the code, no document | Inherit it. Match the neighbours. |
| **Open look** | Nothing to inherit, or the person asked for a new look | Run a tasting in step 3. |

When `DESIGN.md` is absent, check the code and neighbouring surfaces. Inherit
any consistent styling you find. A blank project with no design guidance or
style to inherit has an open look. A new section, component, or state inherits
its existing surface. A redesign keeps the content, function, and brand
commitments while replacing the look.

Name the surface's job. It sets how much expression the surface can carry.

- **Decide:** the viewer decides and acts. Landing pages, pricing, pitch
  slides. Expression earns attention here.
- **Do:** the viewer completes a task. App screens, dashboards, forms,
  settings. Density, consistency, and familiar patterns outrank expression.
- **Understand:** the viewer learns something. Docs, reports, diagrams,
  teaching slides. Structure and reading comfort come first.

Judge the surface, not the product. A developer tool's landing page is Decide.
A fashion brand's help page is Understand.

## 2. Settle the brief

Write four lines: the subject, the audience, the one thing the viewer should do
or understand, and the real content available (copy, data, images, product
screenshots). Take them from the request and the project first.

Ask only for a missing item that would change the result. Ask once, at most
three questions, about the product and its audience. When nobody can answer,
state your assumptions at the top of the report and continue.

Design with the real content, including its worst cases: a long name, an empty
list, a very large number. Mark any value you had to assume.

## 3. Open look: run a tasting

Read [tasting.md](references/tasting.md) before you build variants. A tasting
is three structurally different variants (five at most) that the person
switches between on screen. They can choose one or combine parts of
several.

Run a tasting only for an open look. Skip it for the other two cases and for a
change too small to have a look, such as one state or a spacing fix.

After you write the variant directions and before you build them, read
[defaults.md](references/defaults.md) and compare. Where a direction matches a
listed default on an axis the brief left free, change that axis to something
this subject justifies.

Show the preview and stop for the person's pick. Proceed without a reply
only if the person delegated the choice or the run is explicitly unattended.
In that case, choose the variant that best fits the brief, keep the others
switchable, and report which one you chose and why.

## 4. Plan, then build

Write a short plan before code:

- **Tokens:** 4 to 6 named colours with their values, the type families and
  their roles, and the spacing and radius scale. In an existing system, list
  the tokens and components you will use.
- **Layout:** the main arrangement at narrow and wide sizes, in words or an
  ASCII sketch.
- **Focus:** the one memorable element (Decide), the primary task path (Do), or
  the reading order (Understand).

Review the plan once against the brief. Revise any part that would suit a
similar project unchanged. Put the expression in one element and keep
everything around it quiet. Then build, to the floor.

## The floor

Every result meets these, whatever its look:

- **States:** each interactive element has hover, focus, active, and disabled
  states. Each data region has loading, empty, and error states.
- **Sizes:** the layout holds from 320 px wide to a large desktop, with no
  sideways scroll and no clipped or overflowing text.
- **Contrast:** body text at 4.5:1 or better, large text and interface icons
  at 3:1 or better. Compute the ratio from the two colour values.
- **Keyboard:** every control is reachable in a sensible order and shows a
  visible focus ring.
- **Motion:** motion answers the viewer's action or marks one moment, and it
  turns off under the reduced-motion setting.
- **Type:** body lines of 45 to 80 characters, clear size steps between
  levels, two type families at most.
- **Copy:** a button names its action ("Save changes"). An action keeps one
  name through the whole flow. An error says what happened and how to fix it.
  An empty state says what to do next.
- **Semantics:** real headings, labels, buttons, and image descriptions.
- **Tokens:** components take colour, spacing, and radius from tokens.

## 5. Look at it

Render the result and view it with the host's browser or screenshot tool at
about 375 px and 1440 px wide, plus 320 px for overflow. Capture only the
surface you are working on. Ask before you capture a page that shows another
person's data.

Check in this order: the brief (required content present, main action or
takeaway findable in seconds), the plan (tokens and layout as committed), then
each floor line. Report a problem only when you can point to the element and
say what you observe.

Fix one kind of problem per round, render again, and look again, because a fix
in one place moves things elsewhere. Stop after three rounds and report what
remains.

Run the checks the project already has: lint, accessibility tests, token lint.
When a check or a render is unavailable, skip it and say so. A result nobody
rendered is reported as visually unverified, with a list of what the person
should look at.

## 6. Record what was decided

Read [design-memory.md](references/design-memory.md) when the person picked a
variant, corrected a visual choice during the session, or the work changed
something a design document describes. Propose the record. Write only what the
person approves.

## Done when

- The case and the job are named, and the existing system was respected or the
  tasting pick is recorded.
- The rendered result was viewed at its shipping sizes, or the report says it
  is visually unverified.
- Every floor line was checked, with each failure fixed or listed.
- After a pick, the other variants and the switcher are gone. Before a pick,
  they are clearly marked as awaiting one.
- The report says what was built, what was checked and how, what remains, and
  which assumptions were made.
