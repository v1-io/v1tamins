# Plan the video with the user

## Resolve the brief

The brief is the set of production choices below. Resolve each choice from the first source that settles it: the current request and the context passed with it, then the user's standing preferences (their instructions, project instructions, or a personal skill that wraps this one), then the fallback. A later source never overrides an earlier one. Keep each choice and its source with the storyboard.

| Choice | Fallback |
|---|---|
| Audience and technical depth | An informed colleague who has not followed the work |
| Angle: question, takeaway, worked example, and visual world | Inferred from the request (see step 2 of `SKILL.md`) |
| Tone and humor | Warm, deadpan, at most one small gag ([style.md](style.md)) |
| Visual style | The illustrated everyday system ([style.md](style.md)) |
| Brand | None. Use the generic recipe |
| Destination and length | A landscape 1080p video whose length the story sets |
| Narration | Provider and voice resolved through [speech.md](speech.md) |

## Interview by default

Interview the user unless one of these applies:

- The request already asks you to decide ("just make it", "you choose", "don't ask me").
- A standing preference says not to interview for explainer videos.
- A calling skill or automation supplies the brief and asks for no questions.
- The host cannot ask the user questions.

In those cases, go to [Decide and proceed](#decide-and-proceed).

Run the interview through `v1-interview-me` as a calling skill. Pass it the context you have, the open choices, your options and recommendation for each, and the skip option below. Act as a creative director pitching ideas, not a form collecting fields.

### Understand the subject first

Before the first question, read the sources and work out how the subject really works: the mechanism, what surprises people, where newcomers go wrong, and which concrete cases show it best. Settle everything the context, project, and sources answer. Ask only about choices that need the user's judgment.

### Pitch the angle

Open with two or three pitches for the video. Each pitch is a takeaway, a worked example, and a visual world or metaphor, with one sentence on why it works and what it gives up. Make the pitches take really different angles, such as showing the failure, the hidden mechanism, or the before and after, not three versions of one idea. Recommend one and say why.

In the same round, ask about brand assets and the destination unless the brief already settles them. See [Discover brand sources](#discover-brand-sources). The destination, such as a chat thread, a meeting, documentation, or social media, sets length, aspect ratio, and how much the captions must carry.

### Refine from the answers

Ask next only about what the chosen pitch leaves open or what the user's answer changed. Let each answer shape the next question:

- When the user merges or rewrites pitches, ask what drew them to the parts they kept, then pitch again around those parts.
- When the user names an audience, ask what that audience already believes or doubts about the subject.
- When the user asks for everything, propose a short series or move the extras into supporting notes, and say what the single video gains.
- When the user supplies a real case, check whether it shows the mechanism better than your example, and say so either way.

Give every question two or three concrete options that only this subject could produce, with a recommendation and its reason. Replace a question any video could get, such as "What tone do you want?", with options for this subject, such as a deadpan joke about the subject's own quirk. Push back once, with a reason, when a choice would weaken the explanation. Offer **Just make it: you decide the rest** in every round. When the user picks it, decide and proceed at once.

### Review the storyboard

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
