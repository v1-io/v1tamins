# Review Board Contract

The brief, ledger, runtime resolution, and autonomy rules for `v1-review-board`. Load after `SKILL.md` when convening a board.

## Contents

- [Peer Roles and Defaults](#peer-roles-and-defaults)
- [Runtime Resolution](#runtime-resolution)
- [Shared Read-Only Brief](#shared-read-only-brief)
- [Fan-Out and Supervision](#fan-out-and-supervision)
- [Convergence Ledger](#convergence-ledger)
- [Autonomy and Guardrails](#autonomy-and-guardrails)

## Peer Roles and Defaults

The board is defined by **roles**, not by fixed model names. Default roster:

| Role | Lens | Default placement |
| --- | --- | --- |
| Deep-review A | `v1-deep-review` structural lens | strongest available coding peer, high reasoning |
| Deep-review B | `v1-deep-review` structural lens | a second coding peer, different model family for genuine independence |
| Harsh-maintainability | thermo-nuclear rubric | Cursor, when installed |

Two-peer down to one-peer boards are valid (e.g. no Cursor → drop the harsh-maintainability lens). The minimum-viable-board floor is one surviving peer (see Autonomy). The user may override the roster, the per-role model, or the lens.

## Runtime Resolution

Resolve all of the following at run time. Commit none of them.

- **Peer availability** — use `v1-phone-a-friend`'s capability audit. Bound the probes; a hung probe is `auth: not checked`, not a block.
- **Models** — from each CLI's `--help` / model list, honoring any user-specified tier. If a peer does not report its actual model, record `model: not reported`.
- **Thermo-nuclear rubric** — glob the Cursor install location, not the Codex/Claude plugin caches:

  ```bash
  # The rubric nests deep — e.g. ~/.cursor/plugins/cache/cursor-public/
  # cursor-team-kit/<hash>/skills/thermo-nuclear-code-quality-review/SKILL.md
  # (~8 levels). A shallow -maxdepth silently misses it; search generously.
  RUBRIC="$(find "$HOME/.cursor" -maxdepth 9 -type f \
    -path "*/skills/thermo-nuclear-code-quality-review/SKILL.md" 2>/dev/null | head -1)"
  # empty -> drop the harsh-maintainability lens and record the degradation
  ```

- **Sibling helper (`peer-run.sh`)** — `v1-review-board` and `v1-phone-a-friend` ship in the same plugin and co-install under one skills root, so resolve the sibling by globbing that root rather than a committed `../` path:

  ```bash
  # peer-run.sh sits at <skills>/v1-phone-a-friend/scripts/peer-run.sh — depth 3
  # below the skills root, so -maxdepth must be >= 3 (it was a too-shallow 2).
  PEER_RUN="$(find "$(dirname "$REVIEW_BOARD_SKILL_DIR")" -maxdepth 4 -type f \
    -path "*/v1-phone-a-friend/scripts/peer-run.sh" 2>/dev/null | head -1)"
  # empty -> fall back to the manual supervised-launch snippet (degrade, don't crash)
  ```

  where `$REVIEW_BOARD_SKILL_DIR` is this skill's own directory, resolved by the host at load time. A missing helper is part of the degrade set — report and use the manual snippet from `v1-phone-a-friend`'s Supervised Local Runs section.

## Shared Read-Only Brief

Build one brief and give the identical text to every peer. Pre-dump the diff once (`git diff <base>...HEAD > "$RUN_DIR/pr.diff"`) so no peer re-derives it.

```text
Act as an independent counterpart reviewer. READ ONLY.
Do not edit, create, commit, push, publish, or mutate anything. Report "Files changed: none".

Repo context: <one line — what the project is and what "good" means here>
What this PR does: <one paragraph>

Review lens: <inline the v1-deep-review structural lens, or the thermo-nuclear rubric for the harsh-maintainability peer — inlined per v1-phone-a-friend's rubric-inline pattern when the named skill is not installed in the peer runtime>

How to read: the diff is pre-dumped at pr.diff; read changed files directly from the working tree.

Return:
- Verdict (durable / ship-with-changes / will-rot) + THE ONE THING
- Findings: severity (P0/P1/P2), file:line, risk, concrete fix
- WHAT TO CUT
- Capability path actually used + the actual model used
```

## Fan-Out and Supervision

Launch every peer concurrently and read-only through `peer-run.sh`, one slug per peer under a single run dir:

```bash
"$PEER_RUN" launch --dir "$RUN_DIR" --slug deep-a -- <peer-A read-only wrapper>
"$PEER_RUN" launch --dir "$RUN_DIR" --slug deep-b -- <peer-B read-only wrapper>
"$PEER_RUN" launch --dir "$RUN_DIR" --slug thermo -- <cursor read-only wrapper>   # when present
```

Poll each slug across turns (`status`), read `verdict` (judged by substantive output, not exit code), and tear down stragglers by recorded PID only. One peer stalling never blocks the others — slugs are isolated. Record which peers completed, were partial, stalled, or were skipped.

## Convergence Ledger

After every peer is complete or stalled, **verify each finding against the working tree before acting on it**, then emit:

```text
| # | Finding                                            | Peers | Disposition          |
| F1 | <one-line finding, file:line>                     | 3/3   | Fix (gating)         |
| F2 | <one-line finding>                                | 2/3   | Fix                  |
| F3 | <one-line finding>                                | 1/3   | Partial — <why>      |
| F4 | <one-line finding>                                | 1/3   | Defer — <why>        |
```

- `Peers` = convergence count across the surviving board. Convergence raises confidence; a lone-peer finding is still verified, never dropped on count alone.
- `Disposition` = Fix / Partial / Defer with a one-line rationale.
- De-duplicate near-identical findings; rank by severity. Note which peer was deepest.

## Autonomy and Guardrails

Three levels; **default `apply`**. Every level is fail-safe. `full-auto` is an explicit opt-in, not the silent default — a public skill should not push agent-authored commits before the user has read a finding.

| Level | Stops after |
| --- | --- |
| `ledger` | the compiled ledger (you decide what to address) |
| `apply` (default) | applying Fix/Partial dispositions and running the gate — stops before commit/push, with the diff + summary for review |
| `full-auto` (opt-in) | commit → push → summary |

Fail-safe rules, enforced whenever the board reaches the mutation step:

- **Announce before acting.** State the autonomy level; under `full-auto`, announce that it will commit and push before doing so.
- **Minimum-viable-board floor.** Zero surviving review peers → do not apply/commit/push; report the degradation and stop.
- **Branch guard (positive detection).** Require a named feature branch: `git rev-parse --abbrev-ref HEAD` ≠ `HEAD` (not detached) and ≠ the resolved default branch. Resolve the default branch explicitly via `git symbolic-ref refs/remotes/origin/HEAD` (or `gh repo view --json defaultBranchRef`) — **do not assume `main`**, or a `master`/`develop`-default repo would treat its default branch as a feature branch. If the default branch cannot be resolved, abort the push rather than guessing. Never infer "feature branch" from "not main."
- **Gate, fail-closed.** Discover the project gate (declared check command, else common test/lint runners). Run it after applying. Commit only when green; never force-push. **No gate confidently identified → drop to `apply` and report**; never push unverified.
- **Commit message** names the peers, the models used, and the deliberate deferrals.

Apply Fix/Partial dispositions in batches, handing findings to `v1-address-review` where they map to its flow; verify the tree is clean of unintended edits before and after.
