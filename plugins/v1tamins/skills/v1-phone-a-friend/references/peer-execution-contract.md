# Peer Execution Contract

Use this contract whenever a peer process is proposed or launched. The
contract keeps discovery, authentication, selection, execution, and local
verification separate so one failure cannot be mistaken for another.

## Discovery result

Run `scripts/peer_catalog.py` before every explicit invocation. It must emit
JSON with `schema: v1-peer-catalog/v1`, `confirmation_required: true`, and one
record per discovered CLI. The result records:

| Axis | Values | Meaning |
| --- | --- | --- |
| installation | `installed`, `unavailable` | Executable presence and version surface. |
| credential policy | `eligible`, `not_authenticated`, `auth_not_verified`, `blocked_api_key_present`, `explicit_api_mode`, `api_key_required`, `not_installed` | Single tagged auth decision. Launch derives from this tag plus catalog/selection. |
| model catalog | `resolved`, `unresolved` | Whether the current provider-owned catalog command returned usable IDs. |
| catalog confidence | `verified`, `unresolved` | Provider catalog command output only; help text is never a catalog source. Unresolved means no model may be invented unless custom `--model` is explicit. |
| launch state | `eligible`, `blocked_api_key_present`, `not_authenticated`, `api_key_required`, `auth_unverified`, `model_unresolved` | Derived candidate readiness. Distinct policy failures stay distinct. |
| runner lifecycle | `running`, `complete`, `empty_output`, `stalled`, `timed_out` | Exact states from `peer-run.sh` status/verdict. |
| execution (parent) | runner lifecycle, or `execution_uncertain` | Parent interpretation when dispatch occurred but lifecycle evidence is ambiguous. Not a runner-emitted state. |

Structured auth probes are provider-owned JSON surfaces only:

- Claude: `auth status` → `loggedIn` / `authMethod`
- Codex: `doctor --json` → credentials details (`stored ChatGPT tokens` / `stored auth mode`)
- Cursor Agent: `status --format json` → `isAuthenticated` / `status`
- Agy: no structured auth probe → `eligible` after policy scrub when installed; ambient keys still require `api_explicit`

The result may list an installed CLI with `auth_not_verified` or
`model_catalog: unresolved`. That is useful evidence, not permission to
launch, except for an explicit custom `--model` when auth policy is `eligible`
or `explicit_api_mode`. Never silently substitute another CLI, model, auth
mode, or prompt.

## Candidate record

Before launch, show the user every field below for the selected candidate:

```text
CLI + version: <runtime result>
Model: <current catalog ID, explicit custom ID, or model_unresolved>
Reasoning: <current supported level, or unresolved>
Role: <structural review | correctness/security | maintainability | research | multimodal>
Prompt: <profile name>, source <path or provider rubric>, digest <sha256>
Permission: readonly | local-verify | isolated-delegate | external
Auth policy: eligible | not_authenticated | auth_not_verified | blocked_api_key_present | explicit_api_mode | api_key_required
Catalog confidence: verified | unresolved
Launch state: eligible | blocked_api_key_present | not_authenticated | api_key_required | auth_unverified | model_unresolved
Deadline: <seconds>
Selection: recommended | alternative | user-named
```

The user must approve the exact roster, model, reasoning level, prompt, auth
mode, and permission before `peer-run.sh launch`. A preview becomes
`context_stale` if the working-tree snapshot, CLI/version, model-catalog
fingerprint, or prompt digest changes after approval; rediscover and ask again.

## Authentication policy

`subscription_native` is the default. Run the selected provider through
`scripts/peer-env.sh --auth-mode subscription_native`; it removes known
user-supplied API-key variables without printing them (via `peer_policy.py`) and
leaves provider-native login state available. The wrapper also closes stdin at
the child boundary. A user-supplied API key is allowed only after the user
selects `api_explicit` for that run. Even then, `peer-env.sh` keeps only the
selected provider's known API-key variables and scrubs every other provider's
keys. The wrapper must report `api_explicit`; it must never claim
subscription-native auth.

Provider-native login and an API key are different facts. A successful CLI
version command proves installation only. A status command can prove auth only
when its structured JSON result is clear; otherwise report `auth_not_verified`.
Do not regex free-form auth prose.

## Launch and lifecycle

1. Save the reviewed prompt and a read-only working-tree snapshot in a
   run-specific scratch directory.
2. Launch exactly the approved command through `peer-run.sh`, with stdin
   closed, a recorded deadline, and a unique slug. Detach with `setsid` when
   available, else Perl `POSIX::setsid`, else `nohup`.
3. Poll `status` or read `verdict --json`; do not branch on provider exit code
   alone. A terminal sentinel plus a real peer answer is `complete` (plain text
   non-whitespace, or a terminal JSON / stream-json answer payload — framing or
   error-only JSON alone is not enough), an empty or answer-less terminal result
   is `empty_output`, a vanished process is `stalled`, and a deadline breach is
   `timed_out`. `status` and `verdict` are pure observation; the watchdog and
   explicit `teardown` own process mutation.
4. If dispatch occurred and lifecycle evidence is ambiguous, the parent reports
   `execution_uncertain`. Do not retry, replace the peer, or fan out another
   run automatically.
5. Tear down only the recorded PID/PGID (PGID only when `peer.session=1`).
   Never use a command-line pattern kill.

Mutation, local verification, and external publication are separate permission
choices. A read-only peer result is advice until the parent verifies its cited
files and evidence locally.
