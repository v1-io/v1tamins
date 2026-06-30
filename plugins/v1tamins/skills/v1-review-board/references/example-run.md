# Example Run

A worked, public-safe walkthrough of one `v1-review-board` run end to end. Placeholders (`<repo>`, `<model-*>`, `<base>`) stand in for runtime-resolved values; nothing here is a committed model name or host path. The live golden transcript from a real run is captured operationally after merge — this example shows the shape an implementer and reviewer can follow.

## Trigger

```
/v1-review-board convene the board on this PR — deep-review on the two coding peers, thermo-nuclear on cursor, then address
```

## Phase 1 — Resolve and audit

- Capability audit (bounded probes): coding peer A `installed, auth verified`; coding peer B `installed, auth verified`; Cursor `installed, auth verified`; a fourth peer `not found`.
- Models resolved from each CLI's model list to the strongest available tier; a second peer chosen from a different model family for independence. No model names committed.
- Thermo-nuclear rubric resolved under `~/.cursor/**/skills/thermo-nuclear-code-quality-review/SKILL.md` → found.
- `peer-run.sh` resolved by globbing the shared skills root for `*/v1-phone-a-friend/scripts/peer-run.sh` → found.

Board roster this run: deep-A, deep-B, thermo (3 peers).

## Phase 2 — Brief and fan out

- One shared read-only brief built; `git diff <base>...HEAD` pre-dumped to `pr.diff`.
- Deep-review lens inlined for deep-A/deep-B; thermo-nuclear rubric inlined for the Cursor peer (peers do not have the named skills installed → `prompt-only fallback`).
- All three launched concurrently, read-only, each detached via `peer-run.sh`:

```text
launched slug=deep-a  ...
launched slug=deep-b  ...
launched slug=thermo  ...
```

- Polled across turns. `deep-a` and `thermo` completed; `deep-b` stalled past its deadline and was torn down by PID. Board proceeds with two surviving peers (above the one-peer floor).

## Phase 3 — Compile the ledger

Each finding verified against the working tree before disposition:

```text
| #  | Finding                                                  | Peers | Disposition       |
| F1 | Example links size by old field; contract uses new field | 2/2   | Fix (gating)      |
| F2 | Duplicated rule across two surfaces will drift           | 1/2   | Partial — keep readable inline |
| F3 | Stale count in a doc comment                             | 1/2   | Fix               |
| F4 | Broader refactor of the module                           | 1/2   | Defer — out of scope |
```

A Cursor finding that looked like a bug was checked against the source and proved a false positive — dropped, not laundered into the ledger.

## Phase 4 — Address (full-auto, fail-safe)

- Announced: "full-auto — will apply F1/F2/F3, run the gate, commit, and push."
- Branch guard: `git rev-parse --abbrev-ref HEAD` → a named feature branch, ≠ default → proceed.
- Applied F1/F3 (Fix) and F2 (Partial) in batches via `v1-address-review`'s flow.
- Gate discovered (project's declared check) and run → green. (Had no gate been found, the run would have dropped to `apply` and stopped before push.)
- Committed naming the peers, models, and the F4 deferral; pushed; posted a summary listing dispositions and the stalled `deep-b`.

## Degraded variants

- **No Cursor:** thermo lens dropped; board runs deep-A/deep-B; ledger records the skip.
- **All peers stall:** below the one-peer floor → no apply/commit/push; the board reports the degradation and stops.
- **No gate detected:** drops to `apply` (stop before push), reports.
- **Detached HEAD:** branch guard aborts before any commit.
