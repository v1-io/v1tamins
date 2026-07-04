---
name: v1-menu
description: Use when unsure which v1tamins skill fits the current situation, or when the user asks which skill to use. A menu of every v1 skill, which one to reach for, and how they chain together.
allowed-tools:
  - Read
  - Grep
  - Glob
---
# V1 Menu

You don't remember every v1 skill, so ask. Read the user's situation, then point them at the right skill or chain below — recommend one, name the runner-up, and say why. This menu is an index, not documentation: each skill's own `SKILL.md` holds the detail.

Skills marked **(explicit)** never fire autonomously — the user must name them. They are the easiest ones to forget, so surface them whenever they fit.

## Building something new (idea → shipped)

1. `/v1-interview-me` — office-hours questioning to flesh out an idea before planning. Hands off to `/v1-learning-from-customers` when the question is real demand, or `/v1-diagnosing-constraints` when a stuck process is the real problem.
2. `/v1-prd` — turn the settled idea or ticket into requirements. `/v1-bare-bones` — strip an overscoped plan to the smallest useful version. `/v1-strategy-review` — challenge assumptions and ambition before committing.
3. Build, driving `/v1-write-tests` for new coverage and `/v1-simplify` before calling it done.
4. Ship: `/v1-pr` **(explicit)** (create the PR), `/v1-pr-description` (title/body), `/v1-land-pr` **(explicit)** (commit → push → CI → ready), `/v1-prove-work` **(explicit)** (record browser proof for the PR).

## Reviewing code

- `/v1-deep-review` — review a branch or PR (code, docs, or config) for merge risk and structural maintainability.
- `/v1-review-board` **(explicit)** — fan review out to multiple peer agents.
- `/v1-address-review` — resolve review comments that already exist.
- `/v1-phone-a-friend` — one second opinion from a counterpart agent.

## Fixing and improving code

- Broken: `/v1-debug` (root-cause errors), `/v1-fix-tests` (failing suite), `/v1-e2e-testing` (browser/E2E and flakes).
- Working but rough: `/v1-simplify` (reuse/quality/efficiency + KISS/DRY/SOLID + cognitive complexity, on the diff or named files), `/v1-deslop` (AI slop), `/v1-hindsight-refactor` (delete the messy fix, reimplement cleanly).

## Research and analysis

- `/v1-deep-research` — multi-source research report. `/v1-autoresearch-skill` **(explicit)** — autonomous optimize-measure-keep loop against a measurable target.
- `/v1-learning-from-customers` — demand evidence and discovery. `/v1-testing-prototypes` — user tests for prototypes. `/v1-diagnosing-constraints` — find the bottleneck in a stuck system.
- `/v1-reviewing-data-graphics` — audit charts and dashboards. `/v1-reviewing-usability` — review a UI or flow for user error.

## Communicating and documenting

- `/v1-stickify` — make copy memorable. `/v1-html-it` — self-contained HTML page or report. `/v1-md2docs` **(explicit)** — markdown to Google Doc.
- `/v1-changelog` — what shipped, from merged PRs. `/v1-docs-freshness` — sync docs after changes.

## Working on skills and prompts

- `/v1-skilling-it` — write or improve a skill. `/v1-canon2skill` — mine source material for skill ideas. `/v1-goldpan` **(explicit)** — pan recent PRs and sessions for compound-worthy lessons.
- `/v1-prompt-engineering` — prompt/system-prompt/hook/skill work for any model or host, including GPT-5.5 and OpenRouter specifics.
- `/v1-shared-language` — extract a domain glossary from the conversation.
