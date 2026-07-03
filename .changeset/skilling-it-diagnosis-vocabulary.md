---
"v1tamins": minor
---

`v1-skilling-it`: add a skill-design diagnosis vocabulary.

New `references/diagnosis.md` imports named failure modes (no-op, duplication, sediment, sprawl, premature completion), the two loads (context vs cognitive), leading words, and the completion criterion's clarity-vs-demand axes, with a symptom→cure table and the two split tests — so skill reviews name the concept instead of trading taste. `SKILL.md` gains a "Reviewing and Diagnosing Skills" section and leading-word guidance in the description rules, and discloses the Common Patterns block to `references/patterns.md` (528→464 lines). The CI changeset gate is scoped to `plugins/v1tamins/skills/`.

`validate-plugin.sh` also gains a **sprawl gate** — it fails any `SKILL.md` over 500 lines (all skills currently pass), operationalizing the one objective failure mode across the whole corpus. Dogfooding the lens across all skills surfaced and fixed: two project-specific leftovers in `v1-debug` (`AIDEV-*` notes, FastAPI-specific line — now generalized), a dead copy-pasted guard in `v1-e2e-testing`, and duplicated lines in `v1-refactor` and `v1-canon2skill` (whose own naming example contradicted its gerund rule). Remaining lower-stakes duplication findings are tracked separately.
