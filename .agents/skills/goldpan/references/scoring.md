# Compound-Worthiness Rubric

This rubric defers to `/ce-compound`'s own schema rather than reinventing one. Pass this file inline to every scout. For PR scoring, also pass the project's `.agents/goldpan-signals.md` if present (calibrated, repo-specific evidence — see [calibration.md](calibration.md)).

## Table of contents
- The authoritative definition
- Hard preconditions (from ce-compound)
- The "fill the schema" test (primary scoring signal)
- Track classification + problem_type taxonomy
- Score: High / Medium / Skip
- Why the verbatim signals matter

## The authoritative definition

A candidate is compound-worthy **iff** it can populate `/ce-compound`'s schema with real, specific values — not hand-waved ones. The schema lives at:

```
~/.claude/plugins/marketplaces/every-marketplace/plugins/compound-engineering/skills/ce-compound/references/schema.yaml
```

and the section structure lives at:

```
~/.claude/plugins/marketplaces/every-marketplace/plugins/compound-engineering/skills/ce-compound/assets/resolution-template.md
```

Open both before scoring borderline candidates. The enums there are not suggestions — they are the contract every solution doc must satisfy.

## Hard preconditions (from ce-compound)

Mirrors `/ce-compound`'s own preconditions. A candidate must satisfy ALL three or it is **Skip**:

1. **Solved** — the problem reached a resolution; a fix landed or a decision was made.
2. **Verified** — the fix was shipped (PR merged, tests passing) or the decision was documented as agreed.
3. **Non-trivial** — would take a fresh agent or engineer more than ~30 minutes to re-derive from cold.

## The "fill the schema" test (primary scoring signal)

For each candidate, mentally fill the bug-track or knowledge-track template. If you cannot give a real, specific value for the required fields, **demote the candidate**.

### Bug track — required fields and sections

| Field / Section | Pass test |
|---|---|
| `problem_type` | Maps to one of: `build_error`, `test_failure`, `runtime_error`, `performance_issue`, `database_issue`, `security_issue`, `ui_bug`, `integration_issue`, `logic_error`. If you have to invent a category, it's not bug track. |
| `symptoms` (1-5) | You can quote 1-5 observable symptoms verbatim — error messages, broken behavior, log lines, stack-trace strings. |
| `root_cause` | Maps cleanly to one of the schema's enum values: `missing_association`, `missing_include`, `missing_index`, `wrong_api`, `scope_issue`, `thread_violation`, `async_timing`, `memory_leak`, `config_error`, `logic_error`, `test_isolation`, `missing_validation`, `missing_permission`, `missing_workflow_step`, `inadequate_documentation`, `missing_tooling`, `incomplete_setup`. **If none of these fit, it's probably not a bug-track candidate.** |
| `resolution_type` | Maps to: `code_fix`, `migration`, `config_change`, `test_fix`, `dependency_update`, `environment_setup`, `workflow_improvement`, `documentation_update`, `tooling_addition`, `seed_data_update`. |
| Section: **What Didn't Work** | At least one failed approach you can cite — from PR body, commit history, or session "tried X, didn't work" turns. **A bug-track doc with no `What Didn't Work` content is half a doc.** Strong candidates always have failed approaches in the trail. |
| Section: **Why This Works** | A non-trivial root-cause explanation — not just "fixed the typo". |
| Section: **Prevention** | A concrete guardrail (test, lint rule, code-review checklist, AIDEV-NOTE comment, or equivalent project-specific marker). |

### Knowledge track — required fields and sections

| Field / Section | Pass test |
|---|---|
| `problem_type` | Maps to one of: `best_practice`, `documentation_gap`, `workflow_issue`, `developer_experience`, `architecture_pattern`, `design_pattern`, `tooling_decision`, `convention`. **Prefer the narrowest applicable value;** `best_practice` is a fallback. If you reach for `best_practice` first, ask whether the candidate is actually a `convention` or `tooling_decision`. |
| `applies_when` (≤5) | You can enumerate the specific conditions where this guidance applies. If "always" is the only honest answer, the guidance is too vague. |
| Section: **Guidance** | A concrete practice/pattern/recommendation with at least one code example. |
| Section: **Why This Matters** | Rationale grounded in a real consequence — past incident, cost, security/correctness exposure — not "it's cleaner". |
| Section: **Examples** | Concrete before/after or usage. |

## Track classification + problem_type taxonomy

| Track | problem_types | Category dir |
|---|---|---|
| **Bug** | `build_error` | `build-errors/` |
| | `test_failure` | `test-failures/` |
| | `runtime_error` | `runtime-errors/` |
| | `performance_issue` | `performance-issues/` |
| | `database_issue` | `database-issues/` |
| | `security_issue` | `security-issues/` |
| | `ui_bug` | `ui-bugs/` |
| | `integration_issue` | `integration-issues/` |
| | `logic_error` | `logic-errors/` |
| **Knowledge** | `best_practice` | `best-practices/` (fallback) |
| | `documentation_gap` | `documentation-gaps/` |
| | `workflow_issue` | `workflow-issues/` |
| | `developer_experience` | `developer-experience/` |
| | `architecture_pattern` | `architecture-patterns/` |
| | `design_pattern` | `design-patterns/` |
| | `tooling_decision` | `tooling-decisions/` |
| | `convention` | `conventions/` |

If a single PR contains both a bug fix AND a new convention/pattern, prefer **two** candidates — one per track.

Note on `component`: ce-compound's schema lists a Rails-flavored component enum (`rails_model`, `rails_controller`, `hotwire_turbo`, etc.). If your project does not fit that enum, treat the field as freeform and use a path-shaped value like `services/auth` or `lib/cache`.

## Score: High / Medium / Skip

Apply the schema test, then weight:

### High

All schema fields can be populated with specific values, **and** at least one of:

- `root_cause` clearly maps to an enum value AND there's substantive `What Didn't Work` content
- The candidate establishes a new `convention`, `architecture_pattern`, `design_pattern`, or `tooling_decision`
- Failed approaches in the trail (PR commit history, session "didn't work" turns) reveal a non-obvious dead end
- The fix added a permanent guardrail (test, code comment marker, runbook, structural test, AGENTS.md / CLAUDE.md edit)

### Medium

Schema is fillable but at least one required section would be thin:

- `What Didn't Work` is empty or trivial
- `Why This Matters` reduces to "it's cleaner" / "best practice"
- The fix is real but the rationale is mostly already captured in the PR description and isn't reusable beyond that PR

### Skip (auto-demote regardless of other signals)

- Cannot map `root_cause` to any enum value AND cannot honestly classify as knowledge-track
- `What Didn't Work` is fabricated to fill space
- `applies_when` would have to be "always"
- Candidate is a refactor, rename, or dependency bump (no new failure mode, no new convention)
- Already covered in the project's solutions docs with no new angle (move to "refresh candidates")
- Work in progress, reverted, or unverified

## Why the verbatim signals matter

The project's `.agents/goldpan-signals.md` (when calibrated) lists detection signals — phrases and diff shapes that frequently appear in compound-worthy PRs *for that team's writing style*. They are **leading indicators**, not the definition. A PR can hit no verbatim signals and still be compound-worthy if it satisfies the schema test (e.g. a tiny tool-docstring change that fixes recursion). Conversely, a PR can hit many verbatim signals and still fail the schema test (e.g. a long body with a `## Root Cause` section that's actually a re-statement of the symptom).

Use the verbatim signals to **shortlist**. Use the schema test to **score**.
