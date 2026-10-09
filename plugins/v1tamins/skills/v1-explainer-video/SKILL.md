---
name: v1-explainer-video
description: Create narrated animated explainers. Use for "make an explainer video", "explain this PR in a video", or "animate this concept with narration".
---

# Explainer video

Produce an understandable video and rebuildable source. Build understanding through visible reasoning, with a visual style suited to the subject. Default to an informed colleague who has not followed the investigation; preserve technical depth when requested.

Use this workflow for a narrated animation, not a screen recording or an interactive HTML walkthrough. A plain "explain this PR" request belongs to `v1-pr-walkthrough`; an explicit video request belongs here.

## 1. Establish the lesson

Before scenes, write three short statements: the viewer's question, what they already know, and what they should understand afterward. Aim for one central takeaway in 60–120 seconds; expand when the subject needs it. Infer these choices from the request unless a missing choice would materially change the explanation.

Verify material claims against the task's sources. Select the evidence needed to explain the takeaway. Put detailed IDs, inventories, and secondary statistics in supporting notes unless the lesson depends on them. Keep caveats that would change the conclusion in the explanation itself.

## 2. Design the visual sequence

Read [storyboard.md](references/storyboard.md) before drafting scenes. For each beat, name what the viewer sees, what visibly changes, what that change explains, and its short narration. Complete the rough sequence before polishing the script or generating final audio.

Use a worked example, comparison, transformation, or process unfolding. Start with the subject's actual inputs and outputs: animate a form entry becoming a document paragraph, for example, before introducing internal architecture. Replace “display this text” scenes with visible reasoning. Follow recognizable objects across scenes when useful; reveal details when the narration needs them. Give each scene one explanatory job and make the ending answer the opening question.

Choose a coherent palette, typography, and visual setting suited to the subject. Use readable labels rather than paragraphs, reserve space for captions, and hold new diagrams long enough to inspect. Motion explains a change or directs attention; stillness gives the viewer time to think. If a scene could explain an unrelated subject unchanged, make its objects and actions more specific while retaining useful familiar analogies.

## 3. Review the rough explanation

Read [review.md](references/review.md), then run its first-viewer pass on rough frames and narration before final production. An independent reviewer sees those first and the brief afterward; a creator reviewing their own work must acknowledge that prior context. Resolve unclear connections and misleading visual implications before polishing. This is a working review, not a new user approval gate or proof of human comprehension.

## 4. Build, narrate, and synchronize

Choose the smallest suitable available toolchain. Inspect installed capabilities before writing renderer-specific code; no renderer or speech SDK is a skill dependency. A lightweight frame renderer can suit document and software explanations; a mathematical animation engine can suit geometry; HTML or canvas can suit interface flows. Keep exact labels and data in a deterministic renderer even when using illustrative footage. Install missing tools only within the task's authorized scope, preferably in a project-local environment.

Write natural spoken sentences, explain unfamiliar terms when introduced, and allow viewing pauses. Cut secondary material before increasing speech speed. Keep displayed terms separate from spoken pronunciations where needed; choose plain-language narration and map visual cues to it rather than forcing filenames into the script.

Read [speech.md](references/speech.md) when selecting narration, generating speech, or synchronizing it. Respect the requested provider or supplied recording; otherwise use a configured tool within the user's authorized scope. If none is available, ask for a choice while continuing the storyboard. Do not silently switch providers or deliver a silent video as if narration succeeded.

Use one timeline based on measured audio, with stable named cues for important visual events. Bind cues to narration segments or verified word timings rather than sentence-array positions. After script changes, verify cues and retime affected visuals. Reuse unchanged audio where practical.

Render a short representative scene first to catch layout, font, timing, and renderer problems. Then render the remaining scenes and assemble with the chosen export tool (FFmpeg is one option). Default to a portable 1080p MP4 with H.264 video, yuv420p, and AAC audio, plus SRT captions. Adapt dimensions and frame rate to the destination.

## 5. Verify and deliver

Run the finished-video pass in [review.md](references/review.md). Inspect busy frames at normal viewing size and transitions; play the finished video with sound. Check pacing, pronunciation, synchronization, captions, and consequential visual claims, separately from technical stream and duration checks with an available media inspector. Report unavailable checks precisely; successful encoding or an agent's clarity review does not establish human understanding.

Deliver the playable video, captions, narration, editable animation source, supporting source notes, and the audio/assets needed to rebuild. Use relative paths, document dependencies and font choices, and check a rebuild from the delivered folder. Include licensed redistributable assets or state how to obtain restricted assets; do not leave essential inputs only in a temporary directory. Use the host's supported video preview and checked local links. Publication remains a separate action unless requested.
