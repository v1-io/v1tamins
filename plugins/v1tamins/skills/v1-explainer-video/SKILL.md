---
name: v1-explainer-video
description: Create narrated animated explainers. Use for "make an explainer video", "explain this PR in a video", or "animate this concept with narration".
---

# Explainer video

Produce an understandable video and rebuildable source. Build understanding through visible reasoning, with a visual style suited to the subject. Default to an informed colleague who has not followed the investigation; preserve technical depth when requested.

Use this workflow for a narrated animation, not a screen recording or an interactive HTML walkthrough. A plain "explain this PR" request belongs to `v1-pr-walkthrough`; an explicit video request belongs here.

When another skill supplies the context, reuse its audience, question, takeaway, example, source evidence, material caveats, and narration preferences. Resolve only missing details; pass these directly in context without requiring a separate handoff file. Verify freshness when the underlying work has changed.

## 1. Establish the lesson

Before scenes, write three short statements: the viewer's question, what they already know, and what they should understand afterward. Use one question, one central takeaway, and one worked example that carries it. Let the story set the length: a short idea may need 90 seconds, and a richer one can run past three minutes when each scene still earns its place. When a brief holds several unrelated questions, pick the one that matters most or propose a short series. Infer these choices from the request unless a missing choice would materially change the explanation.

Verify material claims against the task's sources. A broad research brief is source material, not a script: select the evidence the worked example needs. Put tool-by-tool inventories, IDs, and secondary statistics in supporting notes unless the lesson depends on them. Keep caveats that would change the conclusion in the explanation itself.

Explain at the level of ideas, not records. Keep ticket, task, and pull-request numbers, version strings, file and field names, and exact counts out of the narration and off the screen unless the viewer will use them. Name things by their role instead: "the parent company", "one task", "the fix". Prefer a familiar analogy or an explicitly hypothetical example over the literal record when it carries the same mechanism. A request for "everything" widens the supporting notes, not the script.

## 2. Design the visual sequence

Read [storyboard.md](references/storyboard.md) before drafting scenes. For each beat, name the object, its state before and after, the action that changes it, what that change explains, and its short narration. Text, bullets, or a screenshot appearing is not a change. Complete the rough sequence before polishing the script or generating final audio.

Use a worked example, comparison, transformation, or process unfolding. Start with the subject's actual inputs and outputs: animate a form entry becoming a document paragraph, for example, before introducing internal architecture. Replace “display this text” scenes with visible reasoning. Follow recognizable objects across scenes when useful; reveal details when the narration needs them. Give each scene one explanatory job and make the ending answer the opening question.

Use the [visual recipe](references/style.md) to choose a coherent palette, typography, and visual setting. Prefer the illustrated everyday system—expressive drawing, subject-specific objects, and restrained dry humor—for queues, handoffs, and similar processes; honor requested styles and use literal interfaces or precise geometry when those explain the subject better. Use readable labels rather than paragraphs, reserve space for captions, and hold new diagrams long enough to inspect. Keep the picture alive with smooth motion that explains a change or directs attention, then hold briefly so the viewer can read. If a scene could explain an unrelated subject unchanged, make its objects and actions more specific while retaining useful familiar analogies.

## 3. Review the rough explanation

Read [review.md](references/review.md), then run its first-viewer pass on rough frames and narration before final production. An independent reviewer sees those first and the brief afterward; a creator reviewing their own work must acknowledge that prior context. Resolve unclear connections and misleading visual implications before polishing. This is a working review, not a new user approval gate or proof of human comprehension.

## 4. Build, narrate, and synchronize

Choose the smallest suitable available toolchain. Inspect installed capabilities before writing renderer-specific code; no renderer or speech SDK is a skill dependency. Use a renderer that draws anti-aliased vector shapes at sub-pixel positions, such as cairo, a canvas, or a mathematical animation engine, so lines stay smooth and motion does not jitter. Do not ship plain raster shape drawing that snaps to whole pixels. Moving text needs the same care: some text calls, such as cairo's `show_text`, fit each letter to the pixel grid on every frame, so letters jump unevenly under a slow camera move. Draw text as outline paths cached once at a fixed scale, and check a label's position across consecutive frames. Animate with eased movement, scale and camera changes, and transitions that carry objects between scenes, not only fades. When a configured image generator is available, generated illustrations can serve as scenery and props. Keep exact labels and data in a deterministic renderer even when using illustrative footage. Install missing tools only within the task's authorized scope, preferably in a project-local environment.

Write natural spoken sentences, explain unfamiliar terms when introduced, and allow viewing pauses. Cut secondary material before increasing speech speed. Keep displayed terms separate from spoken pronunciations where needed; choose plain-language narration and map visual cues to it rather than forcing filenames into the script.

Read [speech.md](references/speech.md) and resolve the provider before generating speech. A provider named in the request, the user's instructions, or a local skill in context wins over whatever is convenient. If it is unavailable, report a specific blocker; never fall back silently to another provider or an operating-system voice, and never deliver a silent video as if narration succeeded.

Use one timeline based on measured audio, with stable named cues for important visual events. Bind cues to narration segments or verified word timings rather than sentence-array positions. After script changes, verify cues and retime affected visuals. Reuse unchanged audio where practical.

Render a short representative scene first to catch layout, font, timing, and renderer problems. Then render the remaining scenes and assemble with the chosen export tool (FFmpeg is one option). Default to a portable 1080p MP4 with H.264 video, yuv420p, and AAC audio, plus SRT captions. Adapt dimensions and frame rate to the destination.

## 5. Verify and deliver

Run the finished-video pass in [review.md](references/review.md). Judge whether the encoded frames explain the lesson separately from technical validity; clean decoding, loudness, captions, and a reproducible rebuild never show that the video communicates. Play it with sound when the host can. Report unavailable or waived checks precisely in the delivery note; they do not block delivery and must not be described as performed.

Deliver the playable video, captions, narration, editable animation source, supporting source notes, and the audio/assets needed to rebuild. Use relative paths, document dependencies and font choices, and check a rebuild from the delivered folder. Include licensed redistributable assets or state how to obtain restricted assets; do not leave essential inputs only in a temporary directory. Use the host's supported video preview and checked local links. Publication remains a separate action unless requested.
