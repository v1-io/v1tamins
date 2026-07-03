# v1tamins

## 0.6.0

### Minor Changes

- e431c2d: `v1-skilling-it`: add a skill-design diagnosis vocabulary.

  New `references/diagnosis.md` imports named failure modes (no-op, duplication, sediment, sprawl, premature completion), the two loads (context vs cognitive), leading words, and the completion criterion's clarity-vs-demand axes, with a symptom→cure table and the two split tests — so skill reviews name the concept instead of trading taste. `SKILL.md` gains a "Reviewing and Diagnosing Skills" section and leading-word guidance in the description rules, and discloses the Common Patterns block to `references/patterns.md` (528→464 lines). The CI changeset gate is scoped to `plugins/v1tamins/skills/`.

  `validate-plugin.sh` also gains a **sprawl gate** — it fails any `SKILL.md` over 500 lines (all skills currently pass), operationalizing the one objective failure mode across the whole corpus. Dogfooding the lens across all skills surfaced and fixed: two project-specific leftovers in `v1-debug` (`AIDEV-*` notes, FastAPI-specific line — now generalized), a dead copy-pasted guard in `v1-e2e-testing`, and duplicated lines in `v1-refactor` and `v1-canon2skill` (whose own naming example contradicted its gerund rule). Remaining lower-stakes duplication findings are tracked separately.

## 0.5.0

### Minor Changes

- 996ecf7: Refactor the interview skill, adopt changesets for releases, and add an out-of-scope knowledge base.

  - **v1-interview-me** now composes a single interview loop (`references/interview-loop.md`) instead of a ~300-line monolith, attaches a recommended answer to every question, and gains an opt-in with-docs mode that writes resolved glossary terms and gated ADRs during the session. `v1-shared-language` supports inline single-term upserts to back it.
  - **Releases** are now changeset-driven: `npm run version` bumps `package.json`, generates `CHANGELOG.md`, and mirrors the version into both runtime plugin manifests. Validation enforces three-way version parity, and CI requires a changeset for plugin content changes — contributors add a changeset instead of hand-bumping manifests.
  - **`.out-of-scope/`** records rejected skill and design directions with durable reasons so they are not re-proposed.
