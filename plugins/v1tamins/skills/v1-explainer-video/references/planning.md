# Plan the video with the user

## Resolve the brief

The brief is the set of production choices below. Resolve each choice from the first source that settles it: the current request and the context passed with it, then the user's standing preferences (their instructions, project instructions, or a personal skill that wraps this one), then the fallback. A later source never overrides an earlier one. Keep each choice and its source with the storyboard.

| Choice | Fallback |
|---|---|
| Objective: who watches, and what they should believe or do afterward | An informed colleague who has not followed the work and should be able to explain the takeaway |
| Angle: hook, takeaway, worked example, and visual world | Inferred from the request (see step 2 of `SKILL.md`) |
| Tone and humor | Warm, deadpan, at most one small gag ([style.md](style.md)) |
| Visual style | The illustrated everyday system ([style.md](style.md)) |
| Brand | None. Use the generic recipe |
| Destination and length | A landscape 1080p video whose length the story sets |
| Must include or avoid | Anonymize private details and label hypothetical examples |
| Narration | Provider and voice resolved through [speech.md](speech.md) |

## Interview by default

Interview the user unless one of these applies:

- The request already asks you to decide ("just make it", "you choose", "don't ask me").
- A standing preference says not to interview for explainer videos.
- A calling skill or automation supplies the brief and asks for no questions.
- The host cannot ask the user questions.

In those cases, go to [Decide and proceed](#decide-and-proceed).

Run the interview through `v1-interview-me` as a calling skill. Pass it the context you have, the open choices, your options and recommendation for each, and the skip option below.

Work as a small agency on the user's side. A strategist finds what the video must achieve, a researcher understands the subject, a creative director pitches ideas, a producer spots constraints early, and a writer and an art director shape the script and the look. The user should feel guided by an insightful collaborator with opinions, not questioned by a form. Say where you are in the process and why each question matters. Aim for two or three rounds before the storyboard; depth comes from better questions, not more of them.

### Do the homework

Before the first question, read the sources and work out how the subject really works: the mechanism, the insight that surprises people, the misconception newcomers hold, and the concrete cases that show it best. Work out what the likely audience believes now and what would change their mind. Settle everything the context, project, and sources answer. Ask only about choices that need the user's judgment.

### Frame the objective and pitch the angle

Open the first round by stating the objective you infer: who watches, what they should believe or do afterward, and the misconception the video must overcome. When the request supports different objectives, such as persuading a decision or teaching a skill, offer them as options.

Then give two or three pitches that serve that objective. Each pitch is an opening hook, a takeaway, a worked example, and a visual world or metaphor, with one sentence on why it works and what it gives up. Make the pitches take really different angles, such as showing the failure, the hidden mechanism, or the before and after, not three versions of one idea. Recommend one and say why.

### Ask what the user would not think to ask

In the same round, ask about brand assets and the destination unless the brief already settles them. See [Discover brand sources](#discover-brand-sources). The destination, such as a chat thread, a meeting, documentation, or social media, sets length, aspect ratio, and how much the captions must carry.

Then pick the one or two questions below that would change this video most, and skip the rest:

- Will people watch without sound, so the pictures and captions must carry the story?
- What should the viewer do next, and should the ending lead there?
- Who must approve the video, and what would make them reject it?
- May it show real names, customer data, screenshots, or unreleased work?
- Is there a real recording, screenshot, or dataset that would beat an illustration?
- Is the subject sensitive enough that humor should drop?
- Will it stand alone, or sit beside a document that carries the detail?

### Refine from the answers

Ask next only about what the chosen pitch leaves open or what the user's answer changed. Let each answer shape the next question:

- When the user merges or rewrites pitches, ask what drew them to the parts they kept, then pitch again around those parts.
- When the user names an audience, ask what that audience already believes or doubts about the subject.
- When the user asks for everything, propose a short series or move the extras into supporting notes, and say what the single video gains.
- When the user supplies a real case, check whether it shows the mechanism better than your example, and say so either way.
- When an answer reveals a different objective, name the shift and reframe the pitches around it.

Give every question two or three concrete options that only this subject could produce, with a recommendation and its reason. Replace a question any video could get, such as "What tone do you want?", with options for this subject, such as a deadpan joke about the subject's own quirk. Push back once, with a reason, when a choice would weaken the video. Offer **Just make it: you decide the rest** in every round. When the user picks it, decide and proceed at once.

### Present the creative brief and storyboard

When the choices are closed, draft the storyboard ([storyboard.md](storyboard.md)) with its narration. Show it with a short creative brief: the objective, the audience and what they believe now, the takeaway, the hook and worked example, tone, look and brand, what to include or avoid, and the destination and length. Mark which choices the user made and which you made. Name the beat you are least sure of and offer an alternative for it. Revise until the user approves or says to just make it. Then continue to rough frames.

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
