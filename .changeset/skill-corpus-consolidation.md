---
"v1tamins": minor
---

Consolidate the skill corpus: merge genuine duplicates and sharpen trigger boundaries without narrowing the toolkit's breadth. No skills retired; no capability lost.

- **U1 — Prompt engineering:** fold `v1-prompt-engineering-v1tamins` into `v1-prompt-engineering`. GPT-5.5 / OpenAI Responses API / OpenRouter knobs move to `references/gpt-5-5-patterns.md` (loaded from the host-identification step); the Instruction-Value-Gate now references its canonical home in `v1-skilling-it`.
- **U2 — Code cleanup:** merge `v1-refactor` and `v1-complexity` into `v1-simplify` — one skill covering reuse/quality/efficiency, KISS/DRY/SOLID, and cognitive complexity, with behavior-preservation as a per-pass rule and the union of triggers.
- **U3 — Review:** fold `v1-code-review` into `v1-deep-review`, now the single in-agent review skill. It reviews any PR (code, docs, config) on both bars — merge risk and structural maintainability — and inherits the GitHub-posting path (`selective_implicit` + `external_write`). The structural rubric moves to `references/structural-review.md` to stay within the 500-line skill limit.

Removes `v1-prompt-engineering-v1tamins`, `v1-refactor`, `v1-complexity`, and `v1-code-review` as standalone skills.
