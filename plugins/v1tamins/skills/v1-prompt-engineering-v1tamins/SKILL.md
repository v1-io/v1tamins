---
name: v1-prompt-engineering-v1tamins
description: Use when writing, migrating, or reviewing prompts, system prompts, commands, hooks, or agent skills for GPT-5.5 workflows, especially OpenAI Responses API or OpenRouter chat/completions hosts. Triggers on "GPT-5.5 prompt", "OpenRouter prompt", "prompt migration", "reasoning effort", "reasoning_details", "OpenAI system prompt".
---
# Prompt Engineering V1tamins

GPT-5.5-first fork of the original `v1-prompt-engineering` skill for assistants, agents, coding workflows, and structured outputs.

Default assumption: the host uses GPT-5.5, but the host API must be identified before applying API-specific advice. Use Responses API guidance when the host supports it; use OpenRouter `chat/completions` guidance when that is the runtime.

## Quick Start

1. Start from the smallest prompt that passes evals.
2. Make three things explicit:
   - requested outcome and success criteria
   - constraints and missing-evidence behavior
   - output contract and stopping conditions
3. Choose `reasoning_effort` from task shape, not instinct.
4. Match the host runtime before adding API-specific guidance:
   - OpenRouter `chat/completions` -> preserve `reasoning_details`, not `phase`
   - Responses API -> `phase` and `previous_response_id` may matter
5. Add only the blocks that fix a measured failure mode.
6. Use the reference files:
   - `references/gpt-5-5-patterns.md` - ready-to-paste GPT-5.5 blocks, migration defaults, runtime notes
   - `references/gpt-5-4-patterns.md` - compatibility guidance for older GPT-5.4 workflows
   - `references/advanced.md` - carry-forward patterns from the original `v1-prompt-engineering` skill

## Instructions

### 1. Classify the workload first

Use one of these workload shapes before writing the prompt:

- `execution` - deterministic transforms, routing, short tool workflows, coding fixes
- `research` - long-context synthesis, evidence gathering, document review
- `long_horizon_agent` - multi-step tool work, coverage-driven batches, paginated retrieval
- `strict_output` - JSON, SQL, XML, OCR boxes, or other parse-sensitive outputs
- `customer_facing` - emails, memos, announcements, support replies

Match the prompt to the workload:

- `execution` - keep it compact; prefer `low` for tool-using paths and reserve `none` for simple transforms/classification
- `research` - define outcome, success criteria, citation rules, and grounding rules; start with `medium`
- `long_horizon_agent` - add outcome-first policy, selective tool persistence, dependency checks, completeness contract, empty-result recovery, and verification loop
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

Keep a prompt instruction only when it maps to a trigger, gate, artifact, command/tool rule, threshold, example, failure mode, or stop rule. Rewrite generic quality language into one of those forms; delete it when no concrete form exists.

### 3. Define the outcome before process

For GPT-5.5, define the target outcome and success criteria before adding process instructions.
Prefer decision rules and stopping conditions over step-by-step choreography.
Keep `ALWAYS` and `NEVER` for true invariants only.

Use an outcome-first block when initiative matters.
Add an instruction-priority block when style, tone, or task shape may change mid-session.
Use `<task_update>` blocks for mid-conversation changes instead of scattering overrides across multiple paragraphs.

### 4. Make tool use disciplined

When correctness depends on tools, tell GPT-5.5:

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

### 8. Tune reasoning and verbosity last

Treat `reasoning_effort` and API-level verbosity as last-mile knobs.
Default guidance:

- `none` - simple transforms/classification where no planning, search, or tool decision remains
- `low` - slightly ambiguous routing or latency-sensitive tool use
- `medium` - research, long-context synthesis, nuanced review
- `high` - only when evals show a clear gain
- `xhigh` - reserve for rare, long, reasoning-heavy work where latency is secondary

Before increasing `reasoning_effort`, first try:

- `<outcome_first_response_policy>`
- `<completeness_contract>`
- `<verification_loop>`
- `<tool_persistence_rules>`

Use prompt-level verbosity controls first. If the host supports `text.verbosity` or an equivalent, verify on examples because GPT-5.5 low verbosity can be more concise than GPT-5.4 low verbosity.

### 9. Match the host runtime before adding API-specific advice

For OpenRouter `chat/completions` style hosts:

- preserve assistant `reasoning_details` across turns when the provider returns them
- preserve tool calls and tool results in order through tool loops
- use `reasoning.effort`, `response_format`, `tools`, `tool_choice`, and `parallel_tool_calls` through the host's chat-completions surface
- prefer prompt-level verbosity controls first; treat API-level verbosity as optional and host-specific
- do not assume `phase`, `previous_response_id`, or compaction exist

For Responses API hosts:

- preserve output items needed for replay, including `phase` when manually replaying reasoning/tool chains
- use Structured Outputs instead of prompt-only JSON schemas when the host supports it
- optimize prompt caching by keeping stable instructions first and dynamic context later
- avoid adding current date/time unless the task needs business-specific temporal context

### 10. Keep coding-agent boundaries explicit

In coding and terminal agents:

- define sparse, high-signal user updates
- keep shell, edit, and patch tool boundaries explicit
- require a lightweight verification step before declaring completion
- clamp list formatting if the host wants flat bullets only

### 11. Write prompt migrations as change sets, not rewrites

When migrating an existing prompt to GPT-5.5:

1. Switch the model first.
2. Pin `reasoning_effort`.
3. Run evals.
4. Replace fixed process instructions with outcome, success criteria, constraints, and stop rules.
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
- Delete standalone exhortations like "be thorough," "be rigorous," or "write high-quality output" unless the prompt also defines the checklist, artifact, threshold, or validation step that makes the instruction observable.
- If the host routes across providers or fallback models, avoid relying on undocumented provider-specific quirks unless the path is pinned.

## Reference Files

- `references/gpt-5-5-patterns.md` - ready-to-paste GPT-5.5 blocks, OpenAI Responses API notes, OpenRouter chat-completions notes, migration defaults
- `references/gpt-5-4-patterns.md` - compatibility blocks for older GPT-5.4 workflows
- `references/advanced.md` - carry-forward agent prompting and persuasion patterns from the original `v1-prompt-engineering` skill
