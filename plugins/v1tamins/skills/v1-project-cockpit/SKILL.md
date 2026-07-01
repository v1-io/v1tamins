---
name: v1-project-cockpit
description: Use when setting up or operating one control document for multi-repo agent work, cross-repository tasks, project wikis, or task tracker coordination. Triggers on "project cockpit", "master controller", "one wiki", "single place to run agents", "cross-repo tasks", "agent control plane".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - TodoWrite
  - AskUserQuestion
---
# Project Cockpit

Turn a project wiki page or repository document into the single operating surface for multi-repo agent work. The cockpit is not a status essay; it is the durable place where agents read scope, pick the next bounded task, record proof, and hand control back.

## Quick Start

1. Pick one cockpit file: existing project wiki page, `PROJECT_COCKPIT.md`, or `docs/project-cockpit.md`.
2. Read repo guidance for every repo listed before proposing work.
3. Inventory active repos, task trackers, and open decisions.
4. Rewrite the cockpit into the template below.
5. Run only one bounded task at a time unless the user explicitly approves parallel work.
6. Reconcile the cockpit after each task with status, proof, links, and the next human decision.

## When to Use

Use this skill when the user wants one place to coordinate agents across repositories, docs, trackers, or project workstreams.

Do not use for:
- A single-repo bug fix or PR review. Use `v1-debug`, `v1-code-review`, or `v1-pr`.
- Weekly learning extraction. Use `v1-goldpan`.
- Writing a domain glossary. Use `v1-shared-language`.
- External tracker writes, messages, or account changes without explicit user approval.

## Cockpit Contract

Keep the cockpit short enough to scan and concrete enough to operate from. Use this structure unless the project already has a stronger convention:

```markdown
# Project Cockpit: <project>

## Operating Rules
- Default scope: <repos / docs / trackers in bounds>
- Approval gates: <what requires human approval>
- Stop rules: <when agents must stop and report>
- Validation: <commands or checks that prove work>

## Current State
| Surface | Status | Evidence | Next action |
| --- | --- | --- | --- |
| <repo-or-doc> | <green / blocked / stale / unknown> | <link or command> | <specific next step> |

## Decision Queue
| Priority | Decision | Options | Owner | Needed by |
| --- | --- | --- | --- | --- |
| P1 | <question> | <A / B / C> | <human or agent> | <trigger or date> |

## Agent Task Queue
| ID | Task | Scope | Gate | Status |
| --- | --- | --- | --- | --- |
| A1 | <bounded task> | <repo/path> | <test/check> | <ready / running / blocked / done> |

## Run Log
| Time | Actor | Action | Proof | Follow-up |
| --- | --- | --- | --- | --- |
| <timestamp> | <agent/human> | <what changed> | <command/link> | <next step> |
```

## Workflow

### 1. Establish the Single Surface

Find the existing project hub before creating a new one. Search for wiki exports, project docs, `README`, `AGENTS.md`, `CLAUDE.md`, tracker docs, and planning files. If multiple surfaces compete, choose one cockpit and make the others point to it rather than duplicating status.

Before writing a new cockpit file, confirm the destination is inside the project scope and safe to commit or edit.

### 2. Inventory Boundaries

For each repo, doc set, or tracker in scope:
- Read local instructions before relying on general assumptions.
- Record the default branch, active feature branch, dirty state, and relevant validation command.
- Mark external systems as `read-only` until the user approves writes.
- Record missing credentials or inaccessible surfaces as blockers, not guesses.

### 3. Convert Loose Work Into Bounded Tasks

Each agent task must fit this shape:
- **Scope:** one repo, document, tracker, or artifact.
- **Input:** the exact file, issue, card, PR, source note, or user request.
- **Gate:** the command, diff, rendered artifact, screenshot, or review that proves completion.
- **Stop rule:** the condition that requires human judgment or external mutation.
- **Output:** a branch, PR, patch, report, updated doc, or explicit no-op finding.

Drop or split tasks that cannot name all five fields.

### 4. Operate From The Cockpit

Before starting work, read the cockpit and choose the highest-priority task whose scope, gate, and stop rule are clear. During work:
- Keep edits inside the named scope.
- Do not launch other agents unless the cockpit or user explicitly authorizes that mode.
- Update the task status only after inspecting the diff or proof.
- Keep the run log factual: action, proof, follow-up.

### 5. Reconcile Trackers

Treat external trackers as evidence unless write approval is explicit. When reconciliation is allowed:
- Read the tracker item before editing it.
- Preserve tracker IDs and existing status semantics.
- Write the smallest status update that links to proof.
- Mirror the result back into the cockpit so the cockpit remains the operating surface.

### 6. Close The Loop

Before reporting done:
1. Re-read the cockpit sections touched by the run.
2. Confirm every completed task has proof.
3. Move ambiguous or judgment-heavy items to the Decision Queue.
4. Record blockers with exact missing access, command failure, or approval needed.
5. State the next runnable task, or say there is none.

## Failure Modes

- **Split-brain status:** multiple docs claim to be current. Fix by choosing one cockpit and demoting the rest to references.
- **Task soup:** tasks lack scope or proof. Fix by rewriting them into the five-field task shape.
- **Silent external mutation:** tracker, calendar, message, or account changes happen without approval. Stop and ask before mutation.
- **Agent drift:** agents start from chat memory instead of the cockpit. Fix by making the cockpit the first read and last write of every run.
- **No proof:** status says done but no command, diff, link, or artifact proves it. Mark as `blocked: proof missing` until verified.

## Example

User asks: "Use the project wiki as the master controller for three repos and the task tracker."

Response shape:
1. Read the wiki page and repo instructions.
2. Build the cockpit tables with the three repos, tracker IDs, validation gates, and approval gates.
3. Pick one ready task and complete it in its repo.
4. Update the cockpit with the branch, PR or report, validation command, and next decision.
5. Leave tracker writes pending unless the user approved external mutation.
