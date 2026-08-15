# Dynamic Model Selection

Model and reasoning choices are runtime data. Do not put a provider model ID,
alias, or assumed effort value in a reusable skill, prompt template, or test
fixture.

## Discovery command

From the installed Phone-a-Friend skill directory, resolve the discovery helper
from that skill path (not the project cwd), then run:

```bash
PEER_CATALOG="<this skill dir>/scripts/peer_catalog.py"
python3 "$PEER_CATALOG" \
  --profile quality \
  --auth-mode subscription_native \
  --prompt-profile structural \
  --prompt-source <resolved-current-rubric>
```

The script checks installed versions, provider-owned catalog commands, structured
auth status probes, and known API-key presence. It accepts only structured
catalog command output and records which shape it read as `catalog_format`:

| `catalog_format` | Shape |
| --- | --- |
| `json` | A JSON document or array of model records. Preferred when the provider offers it. |
| `tsv` | Tab-separated `id<TAB>label` rows. The ID is the first field; a trailing qualifier in the label may name the reasoning level. |
| `id_dash_label` | `id - label` rows, as a dedicated list command emits. |
| `lines` | One model name per line. |
| `unresolved` | Nothing parsed as a catalog. |

Help text is not a catalog source. A level named in a label seeds a reasoning
level only when the model ID does not already encode one, and only from the
label's trailing qualifier, so a limit mentioned earlier in the text is not read
as a level.

## Alias selection and launch representation

A provider with no catalog command selects by alias: the user names the model,
the result records `representation: alias`, and model confidence stays
`unresolved`. That is a resolved selection, not `model_unresolved`. Installed
catalog-less providers the user has not named still appear as Candidates with
`launch_state=model_unresolved`; they are never dropped into silent
`selection_errors`.

Every candidate also records the exact `launch_model_argument` the installed CLI
will receive. Selection never synthesizes one:

- When the provider has its own reasoning option, the model argument is the
  model ID and the level travels in that option.
- When it does not, the level can only be reached through the model ID itself.
  Ranking prefers a model whose ID already carries the level, and a selected
  pair that no argument can express is `launch_unrepresentable` — visible as an
  alternative, never launched.

Selection and `scripts/peer_launch.py` apply this same rule, so a proposal
cannot promise a level the wrapper is unable to send.

Current provider surfaces are discovered rather than copied into this file:

| Runtime | Preferred model surface | Auth surface | Boundary |
| --- | --- | --- | --- |
| Claude Code | Provider-owned catalog when available; otherwise a user-named alias | `auth status` JSON (`loggedIn`, `authMethod`) | Ambient API keys in subscription mode are a policy block; do not invent models from help. Carries its own reasoning option. |
| Codex | Provider-owned catalog when available; otherwise a user-named alias | `doctor --json` credentials check (`stored ChatGPT tokens` / `stored auth mode`) | Do not invent a model from the parent ChatGPT session or free-form status prose. No separate reasoning option, so the level must be part of the model ID. |
| Cursor Agent | `--list-models` (`id - label` lines) | `status --format json` (`isAuthenticated` / `status`) | Browser login and API-key auth are separate. The model argument is used exactly as the catalog listed it. |
| Antigravity CLI (`agy`) | `models` list command | No structured auth probe; subscription mode is launchable after proposal confirmation once the catalog resolves. Ambient keys still require `api_explicit`. | Use Agy's supported native login path; do not assume another Google CLI's login state applies. |

Custom profile with an explicit `--model` may use a synthetic model entry when
the catalog is unresolved. Mark model confidence `unresolved`. Launch remains
`eligible` only when auth policy is `eligible` or `explicit_api_mode`.

The output contains a CLI/version fingerprint, catalog fingerprint, model ID,
model family, supported reasoning levels, auth `policy_state`, `launch_state`,
role, permission, catalog/model confidence, and a prompt-resolution record.
Preserve those values in the run receipt. A missing prompt source is
`degraded`; no prompt source is `unresolved` and must be resolved before
launch.

## Selection profiles

Profiles are policies, not pinned models:

| Profile | Selection rule | Default use |
| --- | --- | --- |
| `quality` | Highest current model quality exposed by the selected CLI and its highest supported reasoning level. Prefer eligible subscription auth, verified catalog confidence, and a different model family for a second peer. | Serious review, architecture, security, migration. |
| `balanced` | A current strong model with a supported reasoning level below the maximum when the catalog exposes one; retain verified auth and role fit. | Normal review or verification. |
| `fast` | The least expensive/lowest-latency current option the runtime can identify, with a low or medium level only when the catalog exposes it. | Cheap sanity checks. |
| `custom` | A user-selected CLI, current or explicitly named model ID, supported reasoning level, prompt profile, auth mode, and permission. | Deliberate exceptions. |

The ranking is opinionated: eligible subscription auth, current catalog
confidence, role fit, and model-family diversity outrank convenience. Reliable
cost or latency data is shown only when the runtime reports it; otherwise use
`unreported`, not a guess.

## Proposal gate

The discovery result is a proposal, not a launch command. Show the recommended
candidate and viable alternatives, then ask the user to choose or reject it.
For an ordinary Phone-a-Friend request, propose one read-only counterpart. For
a Review Board request, the Board may ask the discovery script for two
distinct coding candidates and show an optional third lens, but it must wait
for an explicit roster selection. A missing or non-eligible preferred candidate
is a visible typed result; it never causes silent replacement or retry.

If the user names a model or reasoning level, validate it against this
invocation's catalog when resolved. Reject unsupported values with the current
alternatives. When the catalog is unresolved, an explicit custom `--model` is
allowed as a synthetic entry with unresolved model confidence. When checking a
prior proposal, pass `--compare-preview <previous.json>` and, when available,
`--snapshot-fingerprint <working-tree-digest>`. A changed catalog, prompt
digest, or snapshot returns `context.status: context_stale`; repeat discovery
and selection before launch.
