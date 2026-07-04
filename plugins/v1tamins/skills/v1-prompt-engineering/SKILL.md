---
name: v1-prompt-engineering
description: Use when writing, reviewing, or migrating prompts, system prompts, hooks, skills, or sub-agent instructions for any model or host. Triggers on "optimize prompt", "system prompt", "GPT-5.5 prompt", "OpenRouter prompt", "reasoning effort", "prompt migration".
---
# Prompt Engineering

Improve prompts by tying every instruction to a concrete failure mode, output contract, or evaluation result.

For GPT-5.5, the OpenAI Responses API, OpenRouter, `reasoning_effort`, or model-migration specifics, load `references/gpt-5-5-patterns.md` (or `references/gpt-5-4-patterns.md` for GPT-5.4 compatibility).

## Quick Start

1. Identify the host, model family, tool surface, and output consumer. For GPT-5.5, OpenAI Responses API, or OpenRouter hosts, load `references/gpt-5-5-patterns.md` (GPT-5.4: `references/gpt-5-4-patterns.md`).
2. Write the smallest prompt that can pass the task.
3. Add only blocks that fix a named failure mode.
4. Test against representative inputs before adding more instruction text.
5. Remove instructions that do not change behavior in test examples.

## Prompt Contract

Every production prompt should define:

| Contract | Include |
| --- | --- |
| Outcome | What the model must produce or decide |
| Inputs | Source material, tools, files, schemas, and trusted context |
| Constraints | Safety, grounding, permissions, latency, or missing-data behavior |
| Output | Exact format, sections, schema, or artifact destination |
| Done | Success criteria and stop conditions |

If a prompt block does not support one of these rows, delete it or move it to documentation outside the prompt.

## Instruction Value Gate

Before keeping an instruction, classify it:

- **Keep:** trigger, gate, artifact, command, threshold, example, failure mode, or stop rule.
- **Rewrite:** vague advice that can become one of those forms.
- **Delete:** generic quality language with no observable decision.

This is the Instruction-Value-Gate / no-op test; `v1-skilling-it` holds the canonical treatment and the full skill failure-mode vocabulary (sediment, sprawl, leading words).

```markdown
# Weak
Be careful and produce a high-quality answer.

# Strong
Before finalizing, verify each required field is present. If a field cannot be derived from the input, output `null` and add the field name to `missing_fields`.
```

## Workflow

### 1. Baseline

Draft the smallest prompt that includes the outcome, inputs, output contract, and missing-information behavior. Do not add examples, role framing, or reasoning instructions yet.

### 2. Evaluate

Run or manually simulate at least three representative cases:

- normal case
- edge or ambiguity case
- missing or conflicting input case

Record what failed: wrong trigger, invented fact, wrong format, excessive verbosity, premature stop, bad tool use, unsafe action, or weak refusal/blocked handling.

### 3. Patch Only The Failure

Use the narrowest pattern that fixes the observed failure:

| Failure | Prompt patch |
| --- | --- |
| Wrong format | Add exact output schema or template |
| Missing fields | Add required-field checklist and missing-field behavior |
| Fabricated facts | Add grounding rule and citation/source constraint |
| Overlong answer | Add section limits or verbosity contract |
| Premature stop | Add completeness contract and blocked-item format |
| Tool misuse | Add tool prerequisites, stop rules, and recovery behavior |
| Weak routing | Add trigger and non-trigger examples |

Avoid adding broad persona language unless the failure is specifically tone, audience, or authority handling.

### 4. Use Examples When Rules Are Ambiguous

Add 2-3 input/output examples when the model must learn a format, boundary, or classification that prose cannot define compactly.

Each example must cover a different decision. Do not include examples that all demonstrate the same obvious case.

### 5. Verify And Prune

After changes, rerun the examples. Keep the change only if it fixes a failure without introducing a worse one.

Then prune:

- repeated constraints
- unsupported performance claims
- generic phrases like "be thorough," "high quality," or "careful"
- reasoning instructions when the output contract already forces the needed work
- confidence scores unless a downstream decision consumes them

## Useful Blocks

### Grounded Answer

```xml
<grounding>
- Use only the provided context and retrieved tool outputs.
- Label inference explicitly.
- If evidence is missing, say what is missing instead of filling the gap.
</grounding>
```

### Structured Output

```xml
<output_contract>
- Output only valid JSON matching the requested schema.
- Do not invent fields.
- Use `null` for unavailable optional values.
- Return an error object when required schema information is missing.
</output_contract>
```

### Tool Workflow

```xml
<tool_rules>
- Use tools only when they materially improve correctness.
- Run prerequisite reads before edits or external actions.
- If a tool returns empty or partial results, try one fallback query before marking the item blocked.
- Ask before irreversible external mutations.
</tool_rules>
```

## Reference Files

- `references/advanced.md` - Carry-forward patterns for context management, degrees of freedom, and prompt discipline.
- `references/gpt-5-5-patterns.md` - GPT-5.5 ready-to-paste blocks, the reasoning-effort ladder, OpenAI Responses API and OpenRouter chat-completions runtime notes, and migration defaults.
- `references/gpt-5-4-patterns.md` - GPT-5.4 compatibility blocks and migration defaults.
