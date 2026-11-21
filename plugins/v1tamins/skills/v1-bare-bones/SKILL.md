---
name: v1-bare-bones
description: Cut plans, PRDs, diffs, branches, PRs, skills, prompts, or architectures to their smallest useful scope. Triggers on "strip this plan", "MVP only", or "strip this PR".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - AskUserQuestion
---
# Bare Bones

Keep the smallest coherent artifact that serves the requested outcome. For a
behavior-preserving code quality pass, deslop, or hindsight rewrite of working
code, use `v1-refine`.

## Set the target and scope

Read the supplied artifact, its directly relevant references, and the smallest
amount of surrounding context needed to judge the cuts. For code, honor a named
file, function, diff, branch, or PR. Resolve a PR's actual base and head, and
compare a branch from its merge base with the intended target branch. With no
named target, use the current diff, including staged and unstaged changes. If
there is no local diff, use the current branch delta when its base is known.
Ask for the target or base if you cannot establish it safely.

Name the requested outcome in one sentence. Identify obligations the cut must
preserve, including safety, correctness, compatibility, and a way to verify the
result. Surface only ambiguities that would change what must stay.

Return a proposal by default. Apply cuts only when the user explicitly
requests edits to local files. Preserve unrelated work. For a branch or PR,
verify that the working tree is on the intended head before editing. If it
isn't, propose a patch against the confirmed revision. Keep commits, pushes,
history rewrites, PR updates, and publication outside this workflow.

## Won't-First Scoping

Start from "Won't Have this time." Put an item back only if the **Must-Have Test**
establishes a specific reason:

- **Usability:** The first useful delivery cannot achieve the stated outcome
  without it.
- **Correctness:** It protects a real safety, privacy, data integrity, or
  compatibility requirement.
- **Validation:** It provides necessary proof the result works.
- **Dependency:** Another required item cannot work without it.
- **No workaround:** A required need has no acceptable existing, manual, or
  temporary path.

Use these tests to judge scope. For working artifacts, also prove that each
cut preserves the behavior and contracts the user still needs. Defer useful
later work. Cut duplicates, speculative options, and ceremony with no current
job. Keep a questionable item in place if its necessity cannot be resolved.
Add no features, requirements, or acceptance criteria.

## Make the cuts

**Plans, PRDs, and proposals.** Keep one end-to-end slice for the requested
outcome. Prefer existing or manual paths where they suffice. Return a
replacement with Goal, Build, Verify, and Non-Goals. Include Blocking Questions
only when an answer is needed to proceed. Cut future phases, platform work,
and rollout ceremony that the slice does not need.

**Code, branches, and PRs.** Review the changed code and trace affected callers,
tests, and public contracts. Reuse existing logic and favor direct control flow.
Propose removing a wrapper, branch, config option, fallback, comment, or test
only when you can show what makes it unnecessary. Look for duplicated logic or
state, branches ruled out by validation or caller contracts, speculative
abstractions, broad casts that hide design problems, narration that explains no
invariant, and test setup or cases that add no proof. Preserve meaningful
coverage, public interfaces, supported inputs, error behavior, side effects,
and real trust boundaries.
Keep scope cuts that change behavior explicit and within what the user
authorized.

Before applying a code cut, establish a focused test, repro, or before/after
check that covers the affected behavior. Run it on the original and on the
revision. If proof is unavailable, leave the cut as a proposal. If the revision
fails the check, correct it or withdraw that cut.

**Skills, prompts, and architectures.** Trace the actual workflow or a
representative end-to-end path. Cut repeated instructions, ceremonial choices,
unneeded handoffs, and layers with no current consumer or responsibility.
Preserve triggers, permissions, required outputs, interfaces, and the owner
of each remaining obligation. Verify that the remaining instructions and
dependencies still reach the intended users and callers.

## Return the result

1. **Cut Scorecard.** Lead with 2–3 short lines. Identify concrete cuts from the
   inspected artifact (files, sections, layers, or lines when counted) and the
   useful slice that remains. Label cuts as proposed or applied and report zero
   when nothing earns removal. Use only counts supported by the artifact.
2. **Revision.** Show the trimmed artifact or concrete diff cuts with file
   locations and reasons. For applied edits, summarize what changed and name
   the check and its result. For proposals, name the check that would verify
   the change.
3. **Scope Ledger.** Use all four labels **Keep / Cut / Defer / Question**.
   Place each significant item in one bucket and write "None" for an empty
   bucket. Use Question for unresolved decisions that affect scope.
