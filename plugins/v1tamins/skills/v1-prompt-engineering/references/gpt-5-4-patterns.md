# GPT-5.4 Deltas (vs GPT-5.5)

For current work, load [`gpt-5-5-patterns.md`](gpt-5-5-patterns.md) first. This file only lists GPT-5.4-specific deltas worth keeping when you are still on 5.4 hosts. Do not duplicate shared contract blocks here.

## Load order

1. `gpt-5-5-patterns.md` — shared contracts, tool-use, research/grounding, OpenRouter/Responses, reasoning ladder, migration.
2. This file — only when the runtime is GPT-5.4 / `gpt-5.4-mini` / `gpt-5.4-nano`.

## Behavior deltas

Relative to 5.5 guidance, GPT-5.4 still benefits from explicit prompting on:
- low-context tool routing early in a session
- dependency-aware workflows with prerequisites
- irreversible or high-impact actions
- coding-agent environments where tool boundaries must stay clear

## 5.4-only prompt blocks

### Default follow-through

```xml
<default_follow_through_policy>
- If the user's intent is clear and the next step is reversible and low-risk, proceed without asking.
- Ask permission only if the next step is:
  (a) irreversible,
  (b) has external side effects, or
  (c) requires missing sensitive information or a choice that would materially change the outcome.
- If proceeding, briefly state what you did and what remains optional.
</default_follow_through_policy>
```

### Mid-conversation task update

Prefer an explicit “current task supersedes earlier task” block when long sessions accumulate conflicting instructions.

### Parallel tool calling + empty-result recovery

Keep parallel-tool and empty-result recovery blocks when evals show 5.4 drops follow-ups after empty tool payloads. Prefer the shared 5.5 wording when both apply.

### Coding-agent autonomy / terminal hygiene

When prompting a coding agent on 5.4, keep explicit autonomy, user-update cadence, terminal hygiene, and flat-bullet formatting blocks if the host does not already inject them.

### Dig deeper nudge

```xml
<dig_deeper_nudge>
- If the user asks to dig deeper, expand evidence and alternatives before concluding.
- Prefer one more retrieval or verification pass over speculative certainty.
</dig_deeper_nudge>
```

### Responses `phase` / compaction

On Responses API hosts still pinned to 5.4: set `phase` correctly so intermediary commentary is not treated as the final answer; use `previous_response_id` and compaction per the 5.5 appendix when available.

## Small-model guidance

### `gpt-5.4-mini`

- Prefer shorter contracts and fewer optional blocks.
- Bias to medium/low `reasoning_effort` unless the task is multi-hop.
- Keep verification loops short and tool lists narrow.

### `gpt-5.4-nano`

- Extremely tight output contracts; avoid parallel multi-tool plans.
- Prefer single-tool steps with explicit stop conditions.
- Skip long research-mode blocks unless retrieval is the whole task.

## Migration

If you can move the host to GPT-5.5, drop this file from the load path and keep only `gpt-5-5-patterns.md`. Starting points from older GPT-5.x setups live in the 5.5 migration table.

## Reference links

- OpenRouter GPT-5.4 migration guide: https://openrouter.ai/docs/guides/evaluate-and-optimize/model-migrations/gpt-5-4
