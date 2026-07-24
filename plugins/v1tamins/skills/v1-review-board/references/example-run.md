# Example Run

A worked, public-safe walkthrough of one `v1-review-board` run end to end. Placeholders (`<repo>`, `<model-*>`, `<base>`) stand in for runtime-resolved values; nothing here is a committed model name or host path. The live golden transcript from a real run is captured operationally after merge — this example shows the shape an implementer and reviewer can follow.

## Trigger

```
/v1-review-board convene a quality board on this PR; show me the current roster first
```

## Phase 1 — Resolve and audit

- `peer_catalog.py` discovers current CLI versions, provider-owned model catalogs, supported reasoning levels, auth sources, read-only workflow support, and fingerprints. One installed CLI reports `model_unresolved`, so it is shown as an alternative but not guessed or launched.
- The `quality` profile recommends two distinct coding CLIs, each with its current catalog model and highest supported reasoning. A maintainability rubric is found and presented as an optional third lens. No model names are committed.
- The prompt sources and the sibling `peer-run.sh` are resolved and fingerprinted; the canonical source and installed runtime are fingerprinted separately.

Proposal shown to the user:

```text
quality (recommended)
  deep-A: <cli-a> <version>, <model-a>, <reasoning-a>, structural review,
          prompt <source-a> <digest-a>, subscription_native, readonly
  deep-B: <cli-b> <version>, <model-b>, <reasoning-b>, correctness/security,
          prompt <source-b> <digest-b>, subscription_native, readonly
  optional: <cli-c> <version>, <model-c>, <reasoning-c>, maintainability,
            prompt <source-c> <digest-c>, subscription_native, readonly

Alternatives: balanced, fast, custom, or remove any candidate.
Selection required: no peer has launched yet.
```

The user selects `deep-A` and `deep-B`, removes the optional third lens, keeps
`subscription_native`, and chooses `ledger`.

Board roster this run: deep-A, deep-B (2 peers).

## Phase 2 — Brief and fan out

- One shared read-only brief built; `git diff <base>...HEAD` pre-dumped to `pr.diff`.
- The selected prompt sources are resolved. A peer without its named workflow is launched only after the user accepts the clearly marked `prompt-only fallback`.
- Exactly the two selected peers launch concurrently, read-only, each detached via `peer-run.sh` with closed stdin and a bounded deadline:

```text
launched slug=deep-a  ...
launched slug=deep-b  ...
```

- Polled across turns. `deep-a` completed; `deep-b` timed out and was torn down by its recorded PID/PGID. The Board records the selected peer's typed failure and does not replace it automatically.

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

## Phase 4 — Address (ledger default; explicit mutation)

- Returned the verified ledger and stopped. The working tree remained unchanged because `ledger` is the default.
- **Apply opt-in:** a separate explicit selection could hand surviving Fix/Partial dispositions to `v1-address-review`, run the gate, and stop before commit/push.
- **Full-auto opt-in:** only a separate explicit selection could announce its intent, re-check the branch guard (named feature branch; default resolved via `git symbolic-ref`, never assumed `main`), commit naming the peers/models/deferrals, and push — never on a red gate, never force-push.

## Degraded variants

- **No Cursor:** thermo lens dropped; board runs deep-A/deep-B; ledger records the skip.
- **All peers stall:** below the one-peer floor → no apply/commit/push; the board reports the degradation and stops.
- **No gate detected:** drops to `apply` (stop before push), reports.
- **Detached HEAD:** branch guard aborts before any commit.
