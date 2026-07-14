# Sources and Deployment

Read this reference when choosing ownership, translating ownership into a
location, or performing any lifecycle stage after source validation.

## Four Independent Contexts

| Context | Question | Never infer it from |
|---|---|---|
| Authoring interface | What can this session read, write, or ask? | Where the skill should live |
| Canonical Source | What durable, identifiable, readable, editable source owns future changes? | The current runtime cache or upload |
| Target runtimes | Which agents must consume the skill? | The authoring interface |
| Deployment Targets | Which installs, uploads, workspaces, or packages are requested now? | The Canonical Source alone |

Resolve all four before deriving paths. An interface may author a skill for a
different runtime, and one Canonical Source may feed several Deployment
Targets.

## Canonical Source Choices

| Choice | Typical owner | Ask or inspect |
|---|---|---|
| Personal/global | One user across projects | Preferred durable skills directory and target runtimes |
| Project or nested package | One repository or subtree | Local instructions, existing skill conventions, package boundary |
| Shared plugin/repository | A team or public distribution | Contribution rules, namespace, metadata, routing, release process |
| Durable managed source | An editable managed workspace | Stable identifier, read/edit capability, export and provenance behavior |
| Custom | User-defined | Durable identifier, readers/editors, and deployment relationship |

Runtime caches, generated installs, opaque uploads, and copied packages are
Deployment Targets. Never edit them as the source of truth. If the chosen
source cannot be persisted from the current interface, return the complete
artifact or handoff as `unpersisted`; do not invent a path.

## Action Parity

Use native blocking-question or file tools when available. Fall back to chat or
a complete unpersisted artifact when unavailable. Equivalent intent must reach
the same gates:

| Action | Filesystem-capable interface | Chat/API-only interface |
|---|---|---|
| Resolve ownership | Inspect explicit source, then ask only missing context | Ask for durable owner and identifier |
| Choose a name | Render 10 candidates in chat; collect number, slug, or custom name | Same |
| Create source | Write after explicit create + resolved source + resolved name | Return an explicitly unpersisted artifact or managed write if supported |
| Audit | Read the full folder without mutation | Review supplied artifact without mutation |
| Deploy | Use the target's mechanism only when requested and authorized | Return a gated handoff when the interface cannot perform it |

## Approval Boundaries

An explicit creation request plus the user's Canonical Source and name choices
authorizes writing that source. Do not add a preview-approval loop. Keep
separate authorization for installation, upload, publication, managed
deployment, remote push, destructive replacement, or any target not requested.
Audit mode is always read-only. Edit mode may mutate only the selected
Canonical Source.

## Status and Drift

Report every target independently with one status:

- `created`: Canonical Source written and re-read successfully.
- `validated`: named validation passed against the current source digest.
- `deployed`: target mutation completed and provenance was verified.
- `failed`: attempted action failed; include the corrective action.
- `inconclusive`: verification was unavailable; never summarize as success.
- `not_requested`: lifecycle stage intentionally not performed.
- `unpersisted`: complete artifact exists only in the response or handoff.

Record source identity or digest before editing or deploying. Re-read it before
write, compare with the captured state, and surface a conflict when it changed.
Retry failed targets individually; never repeat an already successful target
blindly. A deployed copy that drifts is still derived—it does not silently
become another Canonical Source.
