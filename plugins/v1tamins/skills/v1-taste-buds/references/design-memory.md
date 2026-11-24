# Design memory

A design decision that is not written down gets made again, differently, in the
next session. The project's own design document is the memory. This skill keeps
no settings of its own.

## Read

Look for `DESIGN.md` at the repository root or in the docs folder, then for any
other design document the project names in its instructions. Token values are
the rule. Prose explains how and why to apply them. When the two disagree,
report the conflict and follow the tokens until the person decides.

## Create

Offer a design document once, when a tasting pick or a new look was built and
the project has none. Create it only on a yes.

Use the public [DESIGN.md format](https://github.com/google-labs-code/design.md):
token values in YAML front matter (`colors`, `typography`, `rounded`,
`spacing`), then short prose sections such as Overview, Colors, Typography,
Layout, Components, and Do's and Don'ts. Write what was built, with the reason
for each choice. Leave out anything nobody decided.

When the project already runs that format's lint command, run it after you
write. Otherwise skip the lint and say so.

## Learn from the session

Run this when the person corrected a visual choice. Read the session from its
first turn and collect:

| Signal | Example | What to record |
| --- | --- | --- |
| A stated correction | "Use a soft shadow, not a border" | The rule, and the reason if they gave one |
| An edit they made themselves | They changed a duration from 400 to 200 | Their value |
| A repeated nudge | "Smaller." "Still too big." "OK." | Where they ended, not the steps |
| A rejection or a pick | "Undo that"; choosing variant B | What to avoid, or the chosen direction |

Keep a correction only when a fresh agent building a different component in
this project would make the same mistake. Skip one-off content choices and
functional bugs.

For each one you keep, write a rule that a newcomer can apply: name the kind
of component, the exact value or token, and the reason. Use the person's reason.
When they gave none, propose one marked as inferred and get it confirmed, since
a wrong reason spreads the rule to cases it does not fit.

When code can detect a violation (a banned value, a raw colour where a token
exists), also propose a check: a lint rule, a token restriction, or a test. A
check runs on every change. Propose it; add tooling only when the person agrees.

## Write only what is approved

Show every proposed rule and document change, and write the approved ones.
When a rule already exists and failed, make it stricter with a number or a
token. Change a value in one place and update the matching prose in the same
edit, so tokens and prose stay in agreement.
