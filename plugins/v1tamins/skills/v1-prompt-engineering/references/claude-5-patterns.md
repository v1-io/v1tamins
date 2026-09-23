# Claude 5 Patterns

Load this file for Claude 5 generation hosts (Claude Opus 5.5, Claude Fable 5.1) or when migrating older Claude prompts to them. Each item names the older habit and what replaces it.

## Reasoning depth

- Thinking is adaptive and always on for Opus 5.5 and Fable 5.1. Set depth with `output_config.effort`, not with prose such as "think step by step" or "think carefully".
- Delete reasoning-trigger phrases when migrating. They add tokens without changing depth.
- Do not ask the model to reproduce or print its reasoning. That request can be refused as `reasoning_extraction`. Ask for the conclusion plus the evidence or checks a reader needs.

## Output format

- Assistant prefill returns a 400 error on Claude 4.6 and later models. Replace prefill tricks (an opening `{` or a forced first word) with structured outputs: `output_config.format` with a JSON schema.
- When the schema is enforced by the API, keep only missing-data rules in the prompt, for example "use `null` when a field cannot be derived".

## Tool use

- Forced `tool_choice` (`any` or a named `tool`) returns a 400 error on Opus 5.5 and Fable 5.1. Use `tool_choice: auto`, a prompt instruction saying when to call the tool, and `strict: true` on the tool definition so arguments match its schema.

## Instruction wording

- Pressure language ("CRITICAL", "YOU MUST", "NEVER") causes over-triggering: the model applies the rule where it does not fit. State each constraint plainly, once, with its reason.
- Remove progress-update suppressors such as "don't narrate" or "no status updates" carried over from older prompts. Specify the final output instead.
- Prefer qualitative length guidance ("one short paragraph", "cover each sub-question") over word or token caps. Caps get treated as targets and cut needed content.

## Migration checklist

1. Remove prefill and forced `tool_choice`; move format to `output_config.format` or strict tools.
2. Replace reasoning phrases with an `output_config.effort` setting.
3. Rewrite emphasized rules as plain constraints with reasons.
4. Delete narration suppressors and hard word caps.
5. Rerun the prompt's representative cases before and after.
