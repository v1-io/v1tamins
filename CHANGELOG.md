# v1tamins

## 0.7.0

### Minor Changes

- 4ea4de4: Consolidate the skill corpus: merge genuine duplicates and sharpen trigger boundaries without narrowing the toolkit's breadth. No skills retired; no capability lost.

  - **U1 — Prompt engineering:** fold `v1-prompt-engineering-v1tamins` into `v1-prompt-engineering`. GPT-5.5 / OpenAI Responses API / OpenRouter knobs move to `references/gpt-5-5-patterns.md` (loaded from the host-identification step); the Instruction-Value-Gate now references its canonical home in `v1-skilling-it`.
  - **U2 — Code cleanup:** merge `v1-refactor` and `v1-complexity` into `v1-simplify` — one skill covering reuse/quality/efficiency, KISS/DRY/SOLID, and cognitive complexity, with behavior-preservation as a per-pass rule and the union of triggers.
  - **U3 — Review:** fold `v1-code-review` into `v1-deep-review`, now the single in-agent review skill. It reviews any PR (code, docs, config) on both bars — merge risk and structural maintainability — and inherits the GitHub-posting path (`selective_implicit` + `external_write`). The structural rubric moves to `references/structural-review.md` to stay within the 500-line skill limit.

  - **U4 — Trigger sharpening:** narrow `v1-diagnosing-constraints` to non-code throughput bottlenecks (software "diagnose this" yields to `v1-debug`); disambiguate `v1-shared-language` (conversation → `LANGUAGE.md` glossary) from the external domain-modeling skill; make `v1-docs-freshness` defer release-note _generation_ to `v1-changelog`; and flip `v1-menu` to `explicit_only`, the single canonical roster.

  - **U5–U6 — Body-health & DRY (no merges):** dedupe `v1-prove-work`'s repeated `SKILL_DIR` bash and trim `v1-interview-me`'s cross-family posture rows; lift the shared review scaffolding (posture, output format, severity tiers) used by `v1-reviewing-usability` and `v1-reviewing-data-graphics` into one `references/review-skeleton.md`; point `v1-fix-tests` at `v1-write-tests` (mock discipline) and `v1-debug` (flaky handling). The two visual reviewers and `fix-tests`/`write-tests` stay separate.

  Removes `v1-prompt-engineering-v1tamins`, `v1-refactor`, `v1-complexity`, and `v1-code-review` as standalone skills (41 → 37).

### Patch Changes

- c387fae: Fix two skill defects surfaced by the diagnosis-lens sweep:

  - **v1-pr** no longer embeds a `gh pr merge --squash` command in its PR-creation flow (it sat before the review steps — a premature merge). Merging is `v1-land-pr`'s job; `v1-pr` stops at a reviewed, open PR. The attribution tagline still carries into the squash-merge commit automatically.
  - **v1-code-review** now declares its `external_write` side effect (it can post reviews via `gh pr review`) and moves to `selective_implicit` posture, matching its sibling `v1-address-review` and the repo's side-effect convention. Adds the required side-effect routing fixture and updates the trigger inventory.

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
