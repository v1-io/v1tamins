# v1tamins

## 0.10.0

### Minor Changes

- d0c4e59: Add `v1-implement-unit`, an explicit orchestration skill that gates on an adequate plan, runs implementation in a separate resumable thread, cycles fresh review-board ledgers through remediation, and uses `v1-land-pr` to reach a mergeable pull request.
- 0926ee0: Rewrite `v1-pr-walkthrough` around a dated self-contained HTML explanation with Background, Intuition, Code, and interactive Quiz sections. Drop the bundled shell/CSS/JS template and JSON renderer in favor of generating the full page directly.

### Patch Changes

- Reduce always-loaded skill routing descriptions, make invocation posture explicit, and document the compact metadata contract.

## 0.9.0

### Minor Changes

- 516d61e: Corpus judo: merge simplify/deslop/hindsight into v1-refine; decompose walkthrough assets; extract address-review Code Factory adapter; collapse GPT-5.4 pattern twin; shared skill-root resolver; enforce undeclared side_effects; delete activation stubs; default v1-pr review to v1-deep-review.
- d991b89: Expand `v1-debug` into a general causal debugging workflow with a required
  assumption audit, a compact six-step loop, and a single domain appendix for
  feedback loops and corrections. Keep explicit routing boundaries with
  `v1-diagnosing-constraints` and `v1-designing-habit-systems`.

## 0.8.0

### Minor Changes

- c7c7e4f: Add `v1-designing-habit-systems`, an evidence-based skill for designing habit, routine, and cadence systems for a person, team, or process — or diagnosing why an existing one keeps failing — from the primary behavior-change research.
- 3713ab5: Add `v1-pr-walkthrough`, a PR explanation skill that generates a throw-away HTML map of touched files and walks the change in execution order.

  Refine the artifact contract so touched files render as a table, connections render as a visual flowchart, and each walkthrough layer includes a relevant PR snippet.

  Add an accessible, responsive HTML template with a validated JSON renderer so future walkthroughs reuse the audited layout and interactions.

- 6ec5646: Redesign `v1-skilling-it` around an explicit Canonical Source, project and managed ownership choices, and separately gated deployment targets.

  Add a ten-option naming slate for unnamed skills, split portable protocol guidance from OpenAI, Anthropic, and v1tamins conventions, and replace unsafe evaluation and executable-resource examples with bounded, fail-closed guidance.

  Add committed workflow cases and a bounded behavior adapter so routing and loaded-skill behavior are verified as separate contracts.

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
