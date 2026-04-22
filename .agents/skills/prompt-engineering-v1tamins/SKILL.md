---
name: prompt-engineering-v1tamins
description: Use when writing, migrating, or reviewing prompts, system prompts, commands, hooks, or agent skills for GPT-5.4, GPT-5.4-mini, or GPT-5.4-nano workflows, especially on OpenRouter chat/completions. Triggers on "GPT-5.4 prompt", "OpenRouter prompt", "prompt migration", "reasoning effort", "reasoning_details", "OpenAI system prompt".
---

# Prompt Engineering V1tamins

GPT-5.4-first fork of the original `prompt-engineering` skill for assistants, agents, coding workflows, and structured outputs.

Default assumption: the host uses GPT-5.4-family models through a chat-style API such as OpenRouter `chat/completions`. Responses-API guidance is secondary and should only be used when the host explicitly says it supports that runtime.

## Quick Start

1. Start from the smallest prompt that passes evals.
2. Make three things explicit:
   - output contract
   - tool-use expectations
   - completion criteria
3. Choose `reasoning_effort` from task shape, not instinct.
4. Match the host runtime before adding API-specific guidance:
   - OpenRouter `chat/completions` -> preserve `reasoning_details`, not `phase`
   - Responses API -> `phase` and `previous_response_id` may matter
5. Add only the blocks that fix a measured failure mode.
6. Use the reference files:
   - `references/gpt-5-4-patterns.md` - ready-to-paste GPT-5.4 blocks, migration defaults, runtime notes
   - `references/advanced.md` - carry-forward patterns from the original `prompt-engineering` skill

## Instructions

### 1. Classify the workload first

Use one of these workload shapes before writing the prompt:

- `execution` - deterministic transforms, routing, short tool workflows, coding fixes
- `research` - long-context synthesis, evidence gathering, document review
- `long_horizon_agent` - multi-step tool work, coverage-driven batches, paginated retrieval
- `strict_output` - JSON, SQL, XML, OCR boxes, or other parse-sensitive outputs
- `customer_facing` - emails, memos, announcements, support replies

Match the prompt to the workload:

- `execution` - keep it compact; prefer `none` or `low`; add a small verification clause for risky actions
- `research` - add `research_mode`, `citation_rules`, and `grounding_rules`; consider `medium` or `high`
- `long_horizon_agent` - add `tool_persistence_rules`, `dependency_checks`, `completeness_contract`, `empty_result_recovery`, and `verification_loop`
- `strict_output` - clamp format hard; output only the target format; validate before finalizing
- `customer_facing` - separate persistent personality from per-response writing controls

### 2. Keep the prompt compact and explicit

Use short, explicit blocks instead of long prose.
Prefer XML-style sections for reusable policies.
Define:

- what the model should produce
- what the model may use
- what counts as done

Do not add background the model already knows.
Do not add blocks that do not change eval results.

### 3. Define defaults up front

Add a default follow-through policy when initiative matters.
Add an instruction-priority block when style, tone, or task shape may change mid-session.
Use `<task_update>` blocks for mid-conversation changes instead of scattering overrides across multiple paragraphs.

### 4. Make tool use disciplined

When correctness depends on tools, tell GPT-5.4:

- when to use tools
- when not to stop
- which steps are prerequisites
- when parallel calls are allowed
- how to recover from empty or partial retrieval

Prefer selective parallelism: parallelize independent evidence gathering, then synthesize before making more calls.

### 5. Force completeness on long tasks

Treat long-horizon tasks as incomplete until every requested item is covered or marked `[blocked]`.
Track batches, pages, or items internally.
If retrieval looks too narrow, try fallback strategies before concluding there are no results.

### 6. Add a lightweight verification loop

Before finalizing, check:

- correctness against the full request
- grounding against provided context or tool outputs
- formatting against the requested schema
- safety for irreversible or side-effecting actions

Use a small verification loop before raising reasoning effort.

### 7. Lock research to evidence

Require citations only from retrieved sources in the current workflow.
Ban fabricated citations, URLs, IDs, quote spans, table names, and fields.
Label inference as inference.
State conflicts explicitly when sources disagree.

### 8. Tune reasoning last

Treat `reasoning_effort` as a last-mile knob.
Default guidance:

- `none` - fast transforms, action selection, short execution tasks
- `low` - slightly ambiguous routing or tool use
- `medium` - research, long-context synthesis, nuanced review
- `high` - only when evals show a clear gain
- `xhigh` - reserve for rare, long, reasoning-heavy work where latency is secondary

Before increasing `reasoning_effort`, first try:

- `<completeness_contract>`
- `<verification_loop>`
- `<tool_persistence_rules>`

### 9. Match the host runtime before adding API-specific advice

Default to chat-style APIs unless the host explicitly says otherwise.

For OpenRouter `chat/completions` style hosts:

- preserve assistant `reasoning_details` across turns when the provider returns them
- preserve tool calls and tool results in order through tool loops
- use `reasoning.effort`, `response_format`, `tools`, `tool_choice`, and `parallel_tool_calls` through the host's chat-completions surface
- prefer prompt-level verbosity controls first; treat API-level verbosity as optional and host-specific
- do not assume `phase`, `previous_response_id`, or compaction exist

Only add Responses-API guidance when the host explicitly supports it.

### 10. Keep coding-agent boundaries explicit

In coding and terminal agents:

- define sparse, high-signal user updates
- keep shell, edit, and patch tool boundaries explicit
- require a lightweight verification step before declaring completion
- clamp list formatting if the host wants flat bullets only

### 11. Write prompt migrations as change sets, not rewrites

When migrating an existing prompt:

1. Switch the model first.
2. Pin `reasoning_effort`.
3. Run evals.
4. Add the smallest missing block.
5. Re-run evals.
6. Repeat one change at a time.

Do not rewrite a working prompt wholesale unless the structure itself is the problem.

## Examples

### Example: execution-heavy coding agent

```xml
<output_contract>
- Return exactly the sections requested, in order.
- Keep progress updates brief.
- Do not treat commentary or working notes as the final answer.
</output_contract>

<tool_persistence_rules>
- Use tools when they materially improve correctness.
- Do not stop early if another tool call is likely to improve correctness.
</tool_persistence_rules>

<verification_loop>
Before finalizing:
- Check correctness.
- Check grounding against tool outputs.
- Check formatting.
- Ask permission before irreversible actions.
</verification_loop>
```

### Example: research assistant

```xml
<research_mode>
- Do research in 3 passes:
  1) Plan
  2) Retrieve
  3) Synthesize
- Stop only when more searching is unlikely to change the conclusion.
</research_mode>

<citation_rules>
- Only cite sources retrieved in the current workflow.
- Never fabricate citations or URLs.
</citation_rules>

<grounding_rules>
- Base claims only on provided context or tool outputs.
- Label inference as inference.
</grounding_rules>
```

### Example: strict JSON output

```xml
<structured_output_contract>
- Output only JSON.
- Do not add prose or markdown fences.
- Validate that braces and brackets are balanced.
- Do not invent fields.
- If required schema information is missing, return an explicit error object.
</structured_output_contract>
```

## Guidelines

- Prefer explicit contracts over vague "be careful" language.
- Prefer short reusable blocks over long explanatory paragraphs.
- Prefer measured prompt changes over intuition-led rewrites.
- Preserve good existing behavior unless the new model breaks it.
- Document why each added block exists and which failure mode it addresses.
- Remove prompt bloat that no longer changes outcomes.
- If the host routes across providers or fallback models, avoid relying on undocumented provider-specific quirks unless the path is pinned.

## Reference Files

- `references/gpt-5-4-patterns.md` - ready-to-paste GPT-5.4 blocks, OpenRouter chat-completions notes, Responses appendix, migration defaults
- `references/advanced.md` - carry-forward agent prompting and persuasion patterns from the original `prompt-engineering` skill
