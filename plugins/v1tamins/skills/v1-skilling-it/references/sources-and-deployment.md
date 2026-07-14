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

## Target Results and Drift

This section is the host-neutral result model. Report every Canonical Source and
Deployment Target independently with an action, an `action_status`, and a
`verification_status`. Host adapters map their operations to these fields; they
do not add status vocabularies.

Action status:

- `not_requested`: the lifecycle action was not requested.
- `blocked`: the action was requested but a permission, dependency, approval, or
  capability gate prevented an attempt.
- `succeeded`: the named action completed. This says nothing about read-back or
  provenance.
- `failed`: the named action was attempted and failed; include the corrective
  action.
- `unpersisted`: a complete source artifact exists only in the response or
  handoff because the interface could not write the Canonical Source.

Verification status:

- `not_requested`: verification was outside the requested stopping point.
- `verified`: read-back or another named check matched the expected source,
  digest, revision, or behavior.
- `unknown`: verification evidence was unavailable. Never summarize this as
  verified.
- `drifted`: observed target state differs from the expected Canonical Source or
  recorded deployment revision.
- `failed`: the named verification ran and failed; include the failed check and
  corrective action.

Reserve `inconclusive` for behavior-evaluation evidence, where a runtime, judge,
or adapter could not produce an assessable verdict. It is not a source or target
status. A completed deployment with unavailable read-back is
`action_status: succeeded` plus `verification_status: unknown`, never
`verified`.

Record source identity or digest before editing or deploying. Re-read it before
write, compare with the captured state, and surface a conflict when it changed.
Retry failed targets individually; never repeat an already successful target
blindly. A deployed copy that drifts is still derived—it does not silently
become another Canonical Source.
