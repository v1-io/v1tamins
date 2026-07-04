# GPT-5.4 Compatibility Patterns

Compatibility prompt blocks and migration defaults for older GPT-5.4 assistants, agents, and coding workflows. For current work, prefer `gpt-5-5-patterns.md`.

## Table of Contents

1. [Behavior notes](#behavior-notes)
2. [Core contract blocks](#core-contract-blocks)
3. [Tool-use and completeness blocks](#tool-use-and-completeness-blocks)
4. [Research and grounding blocks](#research-and-grounding-blocks)
5. [Coding-agent blocks](#coding-agent-blocks)
6. [OpenRouter chat-completions notes](#openrouter-chat-completions-notes)
7. [Responses API appendix](#responses-api-appendix)
8. [Reasoning and migration defaults](#reasoning-and-migration-defaults)
9. [Small-model guidance](#small-model-guidance)
10. [Reference links](#reference-links)

## Behavior notes

### Where GPT-5.4 is strongest

- strong tone and personality adherence with less drift
- reliable multi-step follow-through on agentic work
- evidence-rich synthesis across long inputs and long sessions
- instruction following when the contract is explicit
- long-context analysis across messy multi-document inputs
- batched or parallel tool calling with good tool-call accuracy
- spreadsheet and finance workflows that need careful formatting and verification

### Where explicit prompting still helps

- low-context tool routing early in a session
- dependency-aware workflows with prerequisites
- choosing `reasoning_effort` by task shape
- research tasks that need citation discipline
- irreversible or high-impact actions
- coding-agent environments where tool boundaries must stay clear

Start with the smallest prompt that passes evals. Add blocks only when they fix a measured failure mode.

## Core contract blocks

### Output contract

```xml
<output_contract>
- Return exactly the sections requested, in the requested order.
- If the prompt defines a preamble, analysis block, or working section, do not treat it as extra output.
- Apply length limits only to the section they are intended for.
- If a format is required (JSON, Markdown, SQL, XML), output only that format.
</output_contract>
```

### Verbosity controls

```xml
<verbosity_controls>
- Prefer concise, information-dense writing.
- Avoid repeating the user's request.
- Keep progress updates brief.
- Do not shorten the answer so aggressively that required evidence, reasoning, or completion checks are omitted.
</verbosity_controls>
```

Use prompt-level verbosity controls as the default. Only lean on API-level verbosity if the host explicitly supports it and your evals show it behaves as expected.

### Default follow-through policy

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

### Instruction priority

```xml
<instruction_priority>
- User instructions override default style, tone, formatting, and initiative preferences.
- Safety, honesty, privacy, and permission constraints do not yield.
- If a newer user instruction conflicts with an earlier one, follow the newer instruction.
- Preserve earlier instructions that do not conflict.
</instruction_priority>
```

### Mid-conversation task update

```xml
<task_update>
For the next response only:
- Do not complete the task.
- Only produce a plan.
- Keep it to 5 bullets.

All earlier instructions still apply unless they conflict with this update.
</task_update>
```

### Personality and writing controls

```xml
<personality_and_writing_controls>
- Persona: <one sentence>
- Channel: <Slack | email | memo | PRD | blog>
- Emotional register: <direct/calm/energized/etc.> + "not <overdo this>"
- Formatting: <ban bullets/headers/markdown if you want prose>
- Length: <hard limit, e.g. <=150 words or 3-5 sentences>
- Default follow-through: if the request is clear and low-risk, proceed without asking permission.
</personality_and_writing_controls>
```

### Memo mode

```xml
<memo_mode>
- Write in a polished, professional memo style.
- Use exact names, dates, entities, and authorities when supported by the record.
- Follow domain-specific structure if one is requested.
- Prefer precise conclusions over generic hedging.
- When uncertainty is real, tie it to the exact missing fact or conflicting source.
- Synthesize across documents rather than summarizing each one independently.
</memo_mode>
```

## Tool-use and completeness blocks

### Tool persistence

```xml
<tool_persistence_rules>
- Use tools whenever they materially improve correctness, completeness, or grounding.
- Do not stop early when another tool call is likely to materially improve correctness or completeness.
- Keep calling tools until:
  (1) the task is complete, and
  (2) verification passes.
- If a tool returns empty or partial results, retry with a different strategy.
</tool_persistence_rules>
```

### Dependency checks

```xml
<dependency_checks>
- Before taking an action, check whether prerequisite discovery, lookup, or memory retrieval steps are required.
- Do not skip prerequisite steps just because the intended final action seems obvious.
- If the task depends on the output of a prior step, resolve that dependency first.
</dependency_checks>
```

### Parallel tool calling

```xml
<parallel_tool_calling>
- When multiple retrieval or lookup steps are independent, prefer parallel tool calls to reduce wall-clock time.
- Do not parallelize steps that have prerequisite dependencies or where one result determines the next action.
- After parallel retrieval, pause to synthesize the results before making more calls.
- Prefer selective parallelism: parallelize independent evidence gathering, not speculative or redundant tool use.
</parallel_tool_calling>
```

### Completeness contract

```xml
<completeness_contract>
- Treat the task as incomplete until all requested items are covered or explicitly marked [blocked].
- Keep an internal checklist of required deliverables.
- For lists, batches, or paginated results:
  - determine expected scope when possible,
  - track processed items or pages,
  - confirm coverage before finalizing.
- If any item is blocked by missing data, mark it [blocked] and state exactly what is missing.
</completeness_contract>
```

### Empty result recovery

```xml
<empty_result_recovery>
If a lookup returns empty, partial, or suspiciously narrow results:
- do not immediately conclude that no results exist,
- try at least one or two fallback strategies,
- only then report that no results were found, along with what you tried.
</empty_result_recovery>
```

### Verification loop

```xml
<verification_loop>
Before finalizing:
- Check correctness: does the output satisfy every requirement?
- Check grounding: are factual claims backed by the provided context or tool outputs?
- Check formatting: does the output match the requested schema or style?
- Check safety and irreversibility: if the next step has external side effects, ask permission first.
</verification_loop>
```

### Missing context gating

```xml
<missing_context_gating>
- If required context is missing, do NOT guess.
- Prefer the appropriate lookup tool when the missing context is retrievable; ask a minimal clarifying question only when it is not.
- If you must proceed, label assumptions explicitly and choose a reversible action.
</missing_context_gating>
```

### Action safety

```xml
<action_safety>
- Pre-flight: summarize the intended action and parameters in 1-2 lines.
- Execute via tool.
- Post-flight: confirm the outcome and any validation that was performed.
</action_safety>
```

## Research and grounding blocks

### Citation rules

```xml
<citation_rules>
- Only cite sources retrieved in the current workflow.
- Never fabricate citations, URLs, IDs, or quote spans.
- Use exactly the citation format required by the host application.
- Attach citations to the specific claims they support, not only at the end.
</citation_rules>
```

### Grounding rules

```xml
<grounding_rules>
- Base claims only on provided context or tool outputs.
- If sources conflict, state the conflict explicitly and attribute each side.
- If the context is insufficient or irrelevant, narrow the answer or say you cannot support the claim.
- If a statement is an inference rather than a directly supported fact, label it as an inference.
</grounding_rules>
```

### Research mode

```xml
<research_mode>
- Do research in 3 passes:
  1) Plan: list 3-6 sub-questions to answer.
  2) Retrieve: search each sub-question and follow 1-2 second-order leads.
  3) Synthesize: resolve contradictions and write the final answer with citations.
- Stop only when more searching is unlikely to change the conclusion.
</research_mode>
```

### Structured output contract

```xml
<structured_output_contract>
- Output only the requested format.
- Do not add prose or markdown fences unless they were requested.
- Validate that parentheses and brackets are balanced.
- Do not invent tables or fields.
- If required schema information is missing, ask for it or return an explicit error object.
</structured_output_contract>
```

### Bounding-box extraction spec

```xml
<bbox_extraction_spec>
- Use the specified coordinate format exactly.
- For each box, include page, label, text snippet, and confidence.
- Add a vertical-drift sanity check so boxes stay aligned with the correct line of text.
- If the layout is dense, process page by page and do a second pass for missed items.
</bbox_extraction_spec>
```

## Coding-agent blocks

### Autonomy and persistence

```xml
<autonomy_and_persistence>
Persist until the task is fully handled end-to-end within the current turn whenever feasible: do not stop at analysis or partial fixes; carry changes through implementation, verification, and a clear explanation of outcomes unless the user explicitly pauses or redirects you.

Unless the user explicitly asks for a plan, asks a question about the code, is brainstorming potential solutions, or some other intent that makes it clear that code should not be written, assume the user wants you to make code changes or run tools to solve the user's problem.
</autonomy_and_persistence>
```

### User updates

```xml
<user_updates_spec>
- Only update the user when starting a new major phase or when something changes the plan.
- Each update: 1 sentence on outcome + 1 sentence on next step.
- Do not narrate routine tool calls.
- Keep the user-facing status short; keep the work exhaustive.
</user_updates_spec>
```

### Terminal tool hygiene

```xml
<terminal_tool_hygiene>
- Only run shell commands via the terminal tool.
- Never "run" tool names as shell commands.
- If a patch or edit tool exists, use it directly; do not attempt it in bash.
- After changes, run a lightweight verification step such as ls, tests, or a build before declaring the task done.
</terminal_tool_hygiene>
```

### Flat bullet formatting

```text
Never use nested bullets. Keep lists flat (single level). If you need hierarchy, split into separate lists or sections. For numbered lists, only use the `1. 2. 3.` style markers.
```

## OpenRouter chat-completions notes

### Default assumption

- If the host does not say otherwise, assume `chat/completions`, not Responses API.
- On OpenRouter, prefer model-level prompting guidance plus chat-completions-compatible params.
- If the host routes across providers or fallback models, keep contracts explicit and rely on evals instead of provider-specific assumptions.

### Reasoning continuity

- Preserve assistant `reasoning_details` across turns when the provider returns them.
- Pass preserved `reasoning_details` back on assistant messages, especially through tool-call loops.
- Keep assistant tool calls and tool results in chronological order.
- Do not assume `phase` or `previous_response_id` exist on this path.
- Do not assume a chat-completions `response_id` is equivalent to Responses API continuation state.

### Parameter surface

- Use `reasoning.effort` as the main reasoning knob.
- Use `response_format` or structured outputs for JSON/schema control.
- Use `tools`, `tool_choice`, and `parallel_tool_calls` for tool workflows.
- Prefer prompt-level `<verbosity_controls>` first.
- Treat API-level verbosity as optional and host-specific.

### Vision and image detail

- Use `high` for normal high-fidelity vision work.
- Use `original` for dense, spatially sensitive, OCR, localization, or computer-use tasks.
- Use `low` only when speed and cost matter more than detail.

## Responses API appendix

Use this section only when the host explicitly supports Responses-style runtimes.

### Phase parameter

- Use `phase` for long-running or tool-heavy assistants that emit commentary before the final answer.
- Preserve assistant `phase` when replaying history.
- Missing `phase` can make GPT-5.4 treat intermediary commentary as the final answer.
- `phase` is not available in chat-completions-only hosts.

### previous_response_id

- Prefer `previous_response_id` when the host supports it.
- If you replay assistant output manually, preserve the original output structure and metadata.
- Do not add `previous_response_id` advice to hosts that only expose message-based chat completions.

### Compaction

- Only relevant if the host exposes Responses API compaction or an equivalent runtime feature.
- Compact after major milestones, not after every small step.
- Treat compacted items as opaque state.
- Keep prompts functionally identical after compaction.

## Reasoning and migration defaults

### Reasoning defaults

- `none` - fast, cost-sensitive execution work
- `low` - latency-sensitive work with mild ambiguity
- `medium` - research, long-context synthesis, nuanced review
- `high` - reserve for tasks that clearly benefit
- `xhigh` - avoid as a default; use only when evals justify the latency and cost

Before increasing `reasoning_effort`, add:

- `<completeness_contract>`
- `<verification_loop>`
- `<tool_persistence_rules>`

### Dig deeper nudge

```xml
<dig_deeper_nudge>
- Don't stop at the first plausible answer.
- Look for second-order issues, edge cases, and missing constraints.
- If the task is safety or accuracy critical, perform at least one verification step.
</dig_deeper_nudge>
```

### Migration sequence

1. Switch the model first.
2. Match the current `reasoning_effort`.
3. Run evals.
4. Add the smallest missing prompt block.
5. Re-run evals.
6. Tune reasoning last.

Suggested starting points:

| Current setup | GPT-5.4 starting point |
|---------------|------------------------|
| `gpt-5.2` | Match the current `reasoning_effort` |
| `gpt-5.3-codex` | Match the current `reasoning_effort` |
| `gpt-4.1` or `gpt-4o` | Start with `none` |
| research-heavy assistants | Start with `medium` or `high` |
| long-horizon agents | Start with `medium` or `high` plus explicit completeness rules |

## Small-model guidance

### `gpt-5.4-mini`

- Put critical rules first.
- Specify the full execution order when tools or side effects matter.
- Do not rely on "you MUST" alone; add structure.
- Separate "do the action" from "report the action."
- Define ambiguity behavior explicitly.
- Specify packaging directly: length, follow-up behavior, citation style, and section order.

### `gpt-5.4-nano`

- Use only for narrow, well-bounded tasks.
- Prefer closed outputs: labels, enums, short JSON, fixed templates.
- Avoid multi-step orchestration unless the flow is extremely constrained.
- Route ambiguous or planning-heavy work to a stronger model instead of over-prompting.

## Reference links

- OpenRouter API reference: https://openrouter.ai/docs/api/reference/overview
- OpenRouter reasoning tokens: https://openrouter.ai/docs/guides/best-practices/reasoning-tokens
- OpenRouter GPT-5.4 migration guide: https://openrouter.ai/docs/guides/evaluate-and-optimize/model-migrations/gpt-5-4
- Latest model guide: https://developers.openai.com/api/docs/guides/latest-model
- Prompt engineering: https://developers.openai.com/api/docs/guides/prompt-engineering
- Compaction: https://developers.openai.com/api/docs/guides/compaction
- Prompt personalities cookbook: https://developers.openai.com/cookbook/examples/gpt-5/prompt_personalities
- Images and vision: https://developers.openai.com/api/docs/guides/images-vision
- Computer use: https://developers.openai.com/api/docs/guides/tools-computer-use
