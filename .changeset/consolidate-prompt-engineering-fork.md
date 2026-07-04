---
"v1tamins": patch
---

Fold `v1-prompt-engineering-v1tamins` into `v1-prompt-engineering` (corpus consolidation U1).

The GPT-5.5-first fork restated ~70% of the general skill's discipline and only added host-specific knobs. Those knobs now live behind progressive disclosure: `v1-prompt-engineering` loads `references/gpt-5-5-patterns.md` (and `gpt-5-4-patterns.md`) when the host is GPT-5.5 / OpenAI Responses API / OpenRouter, keyed off its existing "identify the host" step. The fork's redundant `advanced.md` is dropped in favor of the general skill's superset. The general skill's description broadens to own the GPT-5.5/OpenRouter triggers, and its Instruction-Value-Gate now references the canonical definition in `v1-skilling-it` rather than restating it. Removes one skill from the corpus (41 → 40) and eliminates the misleadingly-named `-v1tamins` fork.
