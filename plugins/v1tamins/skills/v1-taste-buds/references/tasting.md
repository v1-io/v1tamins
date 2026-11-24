# Running a tasting

A tasting answers one question: what should this look like? It is throwaway
work. Its only output is the person's pick.

## 1. Set the directions before you build

Default to three variants. Five is the cap; beyond that the differences turn
into noise.

Write one line per variant before any code: a short name, what leads the
surface, 4 to 6 colour values, the type families, and the reason this direction
suits the subject. Take each direction from the subject's own world: its
materials, its trade, the words its audience uses, the real product. A style
picked from a catalogue fits any subject and therefore none.

Give each variant a different lead so they cannot converge:

- one led by **type** (the words carry the surface),
- one led by **the real thing** (the product, a photograph, live data),
- one led by **structure** (a strong grid, a diagram, a dense working layout).

Variants differ in at least two of these: layout structure, what the viewer
reads first, the primary control, density, and tone. A change of colour alone
is the same variant twice. When two variants come out alike, rebuild one from a
different lead.

Keep the content identical across variants, so the person compares looks and
not copy.

## 2. Build the smallest surface that shows the look

Build enough to judge the look: for a page, the first screen and one content
section; for an app screen, the screen with real data; for a component, the
component in its real surroundings. Meet contrast and narrow-width basics now.
The full floor comes after the pick.

Put the variants where the real thing will live:

| Situation | Where the variants go |
| --- | --- |
| A page or screen that already exists | The same route, chosen by a `?variant=` URL parameter. Data loading, layout chrome, and navigation stay as they are. |
| Something new inside an existing app | Mounted inside the page it will belong to, with the same parameter. |
| A new standalone page | One file or one clearly named throwaway route, following the project's routing convention. |
| A single component | One preview page that shows the variants side by side in a realistic container. |

Prefer a real page with real neighbours. A variant alone on an empty route
looks fine and tells the person little.

Name the files and routes so that anyone can see they are a tasting, for
example with `tasting` or `prototype` in the name.

## 3. Add the switcher

Add one floating bar fixed to the bottom of the screen. It shows each variant's
name and one-line direction, marks the current one, and switches on click and
on the left and right arrow keys. It reads and writes the `?variant=` URL
parameter, so a link opens a specific variant.

Keep the bar visually plain and identical across variants. It is a tool, not
part of any design.

## 4. Hand over and stop

Tell the person how to open the tasting in one step: one command or one file.
List the variants with their one-line directions. Ask which they pick, and say
that they can combine parts.

Then stop for their pick. If the person delegated the choice or the run is
explicitly unattended, follow the continuation rule in step 3 of the skill.

## 5. After the pick

- Fold the chosen direction into the real code and build it to the full floor.
- When the person combines variants, write the combined direction in a few
  lines and confirm it before you build.
- Delete the other variants and the switcher.
- Record the direction through [design-memory.md](design-memory.md) as step 6
  of the skill describes.
