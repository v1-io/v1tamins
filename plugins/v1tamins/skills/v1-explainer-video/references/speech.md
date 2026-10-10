# Narration and timing

## Choose an available path

1. Respect the user's supplied recording or requested provider. Supplied audio does not need synthesis; preserve it and align the visuals to it. If a requested provider is unavailable, explain the missing capability instead of substituting another service.
2. Otherwise use an available configured speech tool within the authorized task. ElevenLabs, MiniMax, other hosted providers, and local speech engines are alternatives, not dependencies. Read the chosen integration's live help or official documentation before using commands or API options.
3. If no usable path exists, ask which provider or recording to use while completing the lesson and storyboard. Report narration as pending. A silent preview is a preview, not the finished narrated deliverable.

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

Keep audio and necessary timing data in the deliverable so it can be rebuilt without calling the provider again. Distinguish successful generation, successful playback, and direct listening in the verification notes.
