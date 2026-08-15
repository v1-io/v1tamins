# Review Board Contract

The brief, ledger, runtime resolution, and autonomy rules for `v1-review-board`. Load after `SKILL.md` when convening a board.

## Contents

- [Peer Roles and Defaults](#peer-roles-and-defaults)
- [Runtime Resolution](#runtime-resolution)
- [Proposal and Selection](#proposal-and-selection)
- [Shared Read-Only Brief](#shared-read-only-brief)
- [Fan-Out and Supervision](#fan-out-and-supervision)
- [Convergence Ledger](#convergence-ledger)
- [Autonomy and Guardrails](#autonomy-and-guardrails)

## Peer Roles and Defaults

The board is defined by **roles and profiles**, not by fixed model names. The
default is a proposal, not an automatic roster:

| Role | Lens | Default placement |
| --- | --- | --- |
| Deep-review A | `v1-deep-review` structural lens | first current eligible coding CLI selected by the `quality` profile |
| Deep-review B | `v1-deep-review` structural lens | second current eligible coding CLI from a different model family |
| Maintainability/multimodal | current maintainability or specialist rubric | optional third candidate when role fit, auth, workflow, and prompt source are verified |

The proposal should prefer two distinct coding CLIs for `quality`, but the user
may choose one, remove the optional third lens, select `balanced`/`fast`, or
provide a `custom` roster. No selection means zero launches and a
`confirmation_required` result. The minimum-viable-board floor is one
surviving peer only after the user has selected a roster.

Do not hardcode model names or reasoning levels in this contract. Resolve both
from the current provider surface and show the exact runtime values in the
proposal.

## Runtime Resolution

Resolve all of the following at every invocation. Commit none of the runtime
values.

- **Peer availability** — run the sibling `v1-phone-a-friend/scripts/peer_catalog.py` with bounded provider probes. Installation, credential policy, model catalog, launch state, and runner lifecycle are separate states.
- **Proposal command** — start with the quality proposal and pass the resolved current prompt source when available. Resolve the catalog helper from the co-installed Phone-a-Friend skill (same skills root), not the project cwd or Review Board's own `scripts/`:

  ```bash
  # peer_catalog.py sits at <skills>/v1-phone-a-friend/scripts/peer_catalog.py
  PEER_CATALOG="$(find "$(dirname "$REVIEW_BOARD_SKILL_DIR")" -maxdepth 4 -type f \
    -path "*/v1-phone-a-friend/scripts/peer_catalog.py" 2>/dev/null | head -1)"
  # empty -> report degrade; do not invent a project-local scripts/ path
  python3 "$PEER_CATALOG" \
    --profile quality \
    --count 2 \
    --auth-mode subscription_native \
    --prompt-profile structural \
    --prompt-source <current-rubric>
  ```

  The result is still `confirmation_required`; `--count 2` describes the proposed roster and does not authorize two launches.
- **Antigravity (`agy`) peer** — prefer its current model catalog for Gemini-backed large-context or multimodal work. Use Agy's native login path; API mode requires an explicit user choice and a documented current surface.
- **Models and reasoning** — use the current provider-owned model catalog or picker. Help text is not a catalog source; no reliable surface is `model_unresolved`. If a peer does not report its actual model, record `model: not reported` rather than treating the requested model as proof.
- **Auth** — use `subscription_native` by default and scrub user API-key variables with `peer-env.sh`. `api_explicit` is a separate user-selected mode. An ambient key in subscription mode is `blocked_api_key_present`, not an invitation to use it.
- **Thermo-nuclear rubric** — glob the Cursor install location, not the Codex/Claude plugin caches:

  ```bash
  # The rubric nests deep — e.g. ~/.cursor/plugins/cache/cursor-public/
  # cursor-team-kit/<hash>/skills/thermo-nuclear-code-quality-review/SKILL.md
  # (~8 levels). A shallow -maxdepth silently misses it; search generously.
  RUBRIC="$(find "$HOME/.cursor" -maxdepth 9 -type f \
    -path "*/skills/thermo-nuclear-code-quality-review/SKILL.md" 2>/dev/null | head -1)"
  # empty -> drop the harsh-maintainability lens and record the degradation
  ```

- **Prompt sources** — resolve the current installed `v1-deep-review`, maintainability, correctness, or specialist rubric; record the source and SHA-256. If unavailable, show a prompt-only fallback and its digest only after the user selects it.
- **Sibling helper (`peer-run.sh`)** — `v1-review-board` and `v1-phone-a-friend` ship in the same plugin and co-install under one skills root, so resolve the sibling by globbing that root rather than a committed `../` path:

  ```bash
  # peer-run.sh sits at <skills>/v1-phone-a-friend/scripts/peer-run.sh — depth 3
  # below the skills root, so -maxdepth must be >= 3 (it was a too-shallow 2).
  PEER_RUN="$(find "$(dirname "$REVIEW_BOARD_SKILL_DIR")" -maxdepth 4 -type f \
    -path "*/v1-phone-a-friend/scripts/peer-run.sh" 2>/dev/null | head -1)"
  # empty -> fall back to the manual supervised-launch snippet (degrade, don't crash)
  ```

  where `$REVIEW_BOARD_SKILL_DIR` is this skill's own directory, resolved by the host at load time. A missing helper is part of the degrade set — report and use the manual snippet from `v1-phone-a-friend`'s Supervised Local Runs section.

## Proposal and Selection

The preflight must show the following for every recommended candidate and
alternative before asking for a roster choice:

| Field | Required value |
| --- | --- |
| CLI | Installed executable and current version. |
| Model | Current catalog ID, alias the user named, or `model_unresolved`; never a guessed name. |
| Launch model argument | The exact value the installed CLI receives, or `launch_unrepresentable`. |
| Reasoning | Highest supported level for the selected profile, or unresolved. |
| Role | Structural review, correctness/security, maintainability, research, or multimodal. |
| Prompt | Named profile, resolved source, and source digest. |
| Permission | `readonly` for the default Board proposal. |
| Auth policy | `eligible`, `not_authenticated`, `auth_not_verified`, `blocked_api_key_present`, `explicit_api_mode`, or `api_key_required`. |
| Launch state | `eligible` or a distinct typed failure such as `model_unresolved` or `launch_unrepresentable`. |
| Catalog confidence | `verified` or `unresolved` from provider catalog commands only. |
| Prompt status | `resolved`, `degraded` (missing source), or `unresolved`. |
| Deadline | Explicit maximum lifecycle. |

Profiles are policies: `quality` chooses the strongest current eligible model
and highest supported reasoning; `balanced` chooses a current strong model with
a lower supported level when available; `fast` chooses the efficient current
option; `custom` requires explicit current values. The quality Board asks for
two distinct coding candidates plus an optional third lens. A candidate with
non-eligible launch state or unresolved prompt evidence stays visible as an
alternative but is not silently replaced.

Discovery, canonical source, installed runtime, model catalog, prompt source,
and working-tree snapshot each receive an independent fingerprint. A changed
fingerprint after the proposal makes the proposal `context_stale`; rediscover
and ask again.

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

After the user selects the exact roster, launch exactly those peers concurrently
and read-only through `peer-run.sh`, one slug per peer under a single run dir:

```bash
"$PEER_RUN" launch --dir "$RUN_DIR" --slug deep-a --deadline-seconds 900 -- <peer-A read-only wrapper>
"$PEER_RUN" launch --dir "$RUN_DIR" --slug deep-b --deadline-seconds 900 -- <peer-B read-only wrapper>
"$PEER_RUN" launch --dir "$RUN_DIR" --slug thermo --deadline-seconds 900 -- <cursor read-only wrapper>   # only if selected
```

Poll each slug across turns (`status`), read `verdict --json` (judged by
substantive output, not exit code), and tear down stragglers by recorded PID
only. One peer stalling never blocks the others — slugs are isolated. Record
which selected peers completed, were partial, timed out, execution-uncertain,
or were skipped. Auth/model/workflow failures do not trigger retries or
replacement fan-out.

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

Three levels; **default `ledger`**. Every level is fail-safe. `apply` and
`full-auto` are explicit opt-ins, and neither is silently chained into
`v1-address-review` or git remote writes before the user chooses it.

| Level | Stops after |
| --- | --- |
| `ledger` | the compiled ledger (you decide what to address) |
| `apply` (explicit) | applying Fix/Partial dispositions and running the gate — stops before commit/push, with the diff + summary for review |
| `full-auto` (opt-in) | commit → push → summary |

Fail-safe rules, enforced whenever the board reaches the mutation step:

- **Announce before acting.** State the autonomy level; under `full-auto`, announce that it will commit and push before doing so.
- **Minimum-viable-board floor.** Zero surviving review peers → do not apply/commit/push; report the degradation and stop.
- **Branch guard (positive detection).** Require a named feature branch: `git rev-parse --abbrev-ref HEAD` ≠ `HEAD` (not detached) and ≠ the resolved default branch. Resolve the default branch explicitly via `git symbolic-ref refs/remotes/origin/HEAD` (or `gh repo view --json defaultBranchRef`) — **do not assume `main`**, or a `master`/`develop`-default repo would treat its default branch as a feature branch. If the default branch cannot be resolved, abort the push rather than guessing. Never infer "feature branch" from "not main."
- **Gate, fail-closed.** Discover the project gate (declared check command, else common test/lint runners). Run it after applying. Commit only when green; never force-push. **No gate confidently identified → drop to `apply` and report**; never push unverified.
- **Commit message** names the peers, the models used, and the deliberate deferrals.

Apply Fix/Partial dispositions in batches, handing findings to `v1-address-review` where they map to its flow; verify the tree is clean of unintended edits before and after.
