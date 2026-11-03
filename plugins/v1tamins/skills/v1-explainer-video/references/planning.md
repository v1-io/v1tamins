# Plan the video with the user

## Resolve the brief

The brief is the set of production choices below. Resolve each choice from the first source that settles it: the current request and the context passed with it, then the user's standing preferences (their instructions, project instructions, or a personal skill that wraps this one), then the fallback. A later source never overrides an earlier one. Keep each choice and its source with the storyboard.

| Choice | Fallback |
|---|---|
| Audience and technical depth | An informed colleague who has not followed the work |
| Question and takeaway | Inferred from the request (see step 2 of `SKILL.md`) |
| Story approach | One worked example that changes on screen |
| Tone and humor | Warm, deadpan, at most one small gag ([style.md](style.md)) |
| Visual style | The illustrated everyday system ([style.md](style.md)) |
| Brand | None. Use the generic recipe |
| Narration | Provider and voice resolved through [speech.md](speech.md) |

## Interview by default

Interview the user unless one of these applies:

- The request already asks you to decide ("just make it", "you choose", "don't ask me").
- A standing preference says not to interview for explainer videos.
- A calling skill or automation supplies the brief and asks for no questions.
- The host cannot ask the user questions.

In those cases, go to [Decide and proceed](#decide-and-proceed).

Run the interview through `v1-interview-me` as a calling skill. Pass it the context you have, the open choices, a recommended answer for each, and the skip option below.

- Look up what the context, project, and sources answer. Ask only about choices that need the user's judgment.
- Ask about brand assets in the first round unless the brief already settles them. See [Discover brand sources](#discover-brand-sources).
- Offer **Just make it: you decide the rest** in every round. When the user picks it, decide and proceed at once.

When the choices are closed, draft the storyboard ([storyboard.md](storyboard.md)) with its narration. Show the user the storyboard table, the narration, and the brief with each choice's source. Revise until the user approves it or says to just make it. Then continue to rough frames.

## Decide and proceed

Fill each open choice with the fallback or with your best judgment for the subject. Do not ask more questions or wait for storyboard approval. In the delivery note, list the choices you made and why, so the user can ask for a revised cut.

Blockers still stop the run: a requested speech provider that is unavailable ([speech.md](speech.md)), or a selected brand source you cannot read.

## Discover brand sources

Before you ask, check the request, the project, and the user's instructions for a brand guide, design tokens, or an asset folder. Offer what you find as the recommended answer. Otherwise recommend **No brand** unless the context names an organization or product whose look the video should match.

Accept any source the user can point to:

| Source | Extract |
|---|---|
| Brand guide or design file, such as a Figma file, PDF, or document | Logo files and usage rules, palette, typefaces, illustration and imagery rules |
| Website | Colors, fonts, logo, and imagery style from the pages or their stylesheets |
| Asset folder, repository, or vault | Logo files, fonts, design tokens, and any written guide |
| Videos, decks, or images to imitate | Palette, type, composition, illustration treatment, and motion. Imitate these traits; do not copy content or reuse assets the user has not supplied |

Read the source with the tools the host has, such as a connector, an export, a browser, or files the user supplies. Write a short brand note: logo files to use, colors and their roles, typefaces and fallbacks, illustration treatment, and anything the source forbids. Mark which parts came from the source and which you inferred. In interview mode, show the brand note with the storyboard.

When only some parts are available, apply those, leave out the rest, and list each gap in the delivery note. Never redraw a logo or guess a brand color. When you cannot read the selected source at all, ask for another route in interview mode, such as an export, screenshots, or the files. Otherwise stop with a blocker that names the source and what failed.
