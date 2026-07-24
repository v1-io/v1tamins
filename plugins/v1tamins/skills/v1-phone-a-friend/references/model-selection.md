# Dynamic Model Selection

Model and reasoning choices are runtime data. Do not put a provider model ID,
alias, or assumed effort value in a reusable skill, prompt template, or test
fixture.

## Discovery command

From the installed Phone-a-Friend skill directory, run:

```bash
python3 scripts/peer_catalog.py \
  --profile quality \
  --auth-mode subscription_native \
  --prompt-profile structural \
  --prompt-source <resolved-current-rubric>
```

The script checks installed versions, provider-owned help/catalog surfaces,
bounded auth status probes, read-only workflow support, and known API-key
presence. It prefers structured model lists or pickers. A documented help
example is a degraded catalog; no usable surface is `model_unresolved`.

Current provider surfaces are discovered rather than copied into this file:

| Runtime | Preferred model surface | Fallback | Boundary |
| --- | --- | --- | --- |
| Claude Code | A provider-owned model picker/catalog when available | Current `--help` examples, marked degraded | Do not use a non-interactive API-key path in subscription mode. |
| Codex | A provider-owned model catalog or structured doctor/config surface when available | Current help only, otherwise unresolved | Do not invent a model from the parent ChatGPT session. |
| Cursor Agent | Its current model-list surface | Current help only, marked degraded | Browser login and API-key auth are separate. |
| Antigravity CLI (`agy`) | Its current model-list command | Current help only, marked degraded | Use Agy's supported native login path; do not assume another Google CLI's login state applies. |

For Codex subscription auth, use the provider-owned `codex login status` surface. Its current model catalog may still be `model_unresolved` when the installed CLI does not expose a usable list command; do not substitute a model from the parent session.

The output contains a CLI/version fingerprint, catalog fingerprint, model ID,
model family, supported reasoning levels, auth source, role, permission,
confidence, and a prompt-resolution record. Preserve those values in the run
receipt. A missing prompt source is `degraded`; no prompt source is
`unresolved` and must be resolved before launch.

## Selection profiles

Profiles are policies, not pinned models:

| Profile | Selection rule | Default use |
| --- | --- | --- |
| `quality` | Highest current model quality exposed by the selected CLI and its highest supported reasoning level. Prefer verified subscription auth, catalog confidence, and a different model family for a second peer. | Serious review, architecture, security, migration. |
| `balanced` | A current strong model with a supported reasoning level below the maximum when the catalog exposes one; retain verified auth and role fit. | Normal review or verification. |
| `fast` | The least expensive/lowest-latency current option the runtime can identify, with a low or medium level only when the catalog exposes it. | Cheap sanity checks. |
| `custom` | A user-selected CLI, current model ID, supported reasoning level, prompt profile, auth mode, and permission. | Deliberate exceptions. |

The ranking is opinionated: subscription-native auth, read-only capability,
current catalog confidence, role fit, and model-family diversity outrank
convenience. Reliable cost or latency data is shown only when the runtime
reports it; otherwise use `unreported`, not a guess.

## Proposal gate

The discovery result is a proposal, not a launch command. Show the recommended
candidate and viable alternatives, then ask the user to choose or reject it.
For an ordinary Phone-a-Friend request, propose one read-only counterpart. For
a Review Board request, the Board may ask the discovery script for two
distinct coding candidates and show an optional third lens, but it must wait
for an explicit roster selection. A missing or ineligible preferred candidate
is a visible typed result; it never causes silent replacement or retry.

If the user names a model or reasoning level, validate it against this
invocation's catalog. Reject unsupported values with the current alternatives.
When checking a prior proposal, pass `--compare-preview <previous.json>` and,
when available, `--snapshot-fingerprint <working-tree-digest>`. A changed
catalog, prompt digest, or snapshot returns `context.status: context_stale`;
repeat discovery and selection before launch.
