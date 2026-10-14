# Narration and timing

## Resolve the provider before generating speech

1. A supplied recording or a provider named in the request wins. A provider or voice named in the user's instructions, project instructions, or a local skill already in context counts as requested; check those before choosing. Supplied audio does not need synthesis; preserve it and align the visuals to it.
2. With no requested provider, use an available configured speech tool within the authorized task. ElevenLabs, MiniMax, other hosted providers, and local speech engines are alternatives, not dependencies. A built-in operating-system voice is a last choice: use it only when nothing else is configured, and name it in the delivery note.
3. If the requested provider is unavailable or fails, stop narration with a specific blocker that names the missing capability. Never substitute another provider or an operating-system voice. If no usable path exists at all, ask which provider or recording to use while completing the lesson and storyboard. A silent preview is a preview, not the finished narrated deliverable.

Read the chosen integration's live help before using commands or options. If live help and the integration's documentation disagree, follow the live help, check whether the installed version is behind the documented one, and report the mismatch to the integration's owner.

Use the host's credential mechanism. Check availability without exposing values; never put credentials in scripts, logs, artifacts, or the delivered package. Configuration alone does not authorize transmitting private content or incurring charges outside the user's scope. Confirm a new provider or spending boundary when it is not already covered. Publication and sharing require their own authorization.

## Keep the rendering boundary small

The renderer needs local audio, the corresponding spoken text, measured duration, and timestamps when available. Keep this information with the project's timeline; no provider adapter framework or skill-specific settings file is needed.

Use one consistent voice and settings unless the lesson calls for multiple speakers. Preserve ordinary spoken phrasing. Separate displayed terms from pronunciation overrides when the tool supports them. Verify names and abbreviations rather than assuming successful synthesis means correct pronunciation.

## Synchronize without requiring transcription

- Use returned word or sentence timestamps when available and check them against the audio.
- When precise timing is absent, synthesize short coherent passages separately and measure each file. This supplies segment boundaries without adding a transcription dependency. Avoid splitting phrases so finely that delivery becomes choppy.
- Add deliberate inspection pauses outside the speech. Choose their length for the visual action; do not copy fixed pause constants into every video.
- Name important cues, such as `reveal_missing_field`, and bind them to a segment boundary or verified offset. Measured segment boundaries do not prove word-level timing inside a segment.
- Derive captions from the actual spoken text and timing. If caption blocks are too dense, use finer verified boundaries or shorten the narration; do not distribute words evenly and call that alignment.
- After an edit, reuse unchanged clips, regenerate changed clips, and recompute dependent timing. Normalize sample format when combining audio from different sources and verify the final export preserves both audio and visual tails.

Keep audio and necessary timing data in the deliverable so it can be rebuilt without calling the provider again. Distinguish successful generation, successful playback, and direct listening in the verification notes. Record the provider and voice used.
