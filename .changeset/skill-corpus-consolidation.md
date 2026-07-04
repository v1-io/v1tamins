---
"v1tamins": minor
---

Consolidate the skill corpus: merge genuine duplicates and sharpen trigger boundaries without narrowing the toolkit's breadth. No skills retired; no capability lost.

- **U1 — Prompt engineering:** fold `v1-prompt-engineering-v1tamins` into `v1-prompt-engineering`. GPT-5.5 / OpenAI Responses API / OpenRouter knobs move to `references/gpt-5-5-patterns.md` (loaded from the host-identification step); the Instruction-Value-Gate now references its canonical home in `v1-skilling-it`.
- **U2 — Code cleanup:** merge `v1-refactor` and `v1-complexity` into `v1-simplify` — one skill covering reuse/quality/efficiency, KISS/DRY/SOLID, and cognitive complexity, with behavior-preservation as a per-pass rule and the union of triggers.
- **U3 — Review:** fold `v1-code-review` into `v1-deep-review`, now the single in-agent review skill. It reviews any PR (code, docs, config) on both bars — merge risk and structural maintainability — and inherits the GitHub-posting path (`selective_implicit` + `external_write`). The structural rubric moves to `references/structural-review.md` to stay within the 500-line skill limit.

- **U4 — Trigger sharpening:** narrow `v1-diagnosing-constraints` to non-code throughput bottlenecks (software "diagnose this" yields to `v1-debug`); disambiguate `v1-shared-language` (conversation → `LANGUAGE.md` glossary) from the external domain-modeling skill; make `v1-docs-freshness` defer release-note *generation* to `v1-changelog`; and flip `v1-menu` to `explicit_only`, the single canonical roster.

- **U5–U6 — Body-health & DRY (no merges):** dedupe `v1-prove-work`'s repeated `SKILL_DIR` bash and trim `v1-interview-me`'s cross-family posture rows; lift the shared review scaffolding (posture, output format, severity tiers) used by `v1-reviewing-usability` and `v1-reviewing-data-graphics` into one `references/review-skeleton.md`; point `v1-fix-tests` at `v1-write-tests` (mock discipline) and `v1-debug` (flaky handling). The two visual reviewers and `fix-tests`/`write-tests` stay separate.

Removes `v1-prompt-engineering-v1tamins`, `v1-refactor`, `v1-complexity`, and `v1-code-review` as standalone skills (41 → 37).
