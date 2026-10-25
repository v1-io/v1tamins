# Composition and change

## Name the relationship and completion owner

| Relationship | Meaning | Completion owner |
|---|---|---|
| Shared knowledge | Several skills read one resource | Each consuming workflow |
| Advisory use | A narrow opinion informs a caller | Caller owns the overall task |
| Delegated subtask | Callee returns a defined artifact the caller checks | Callee owns subtask; caller owns overall result |
| Workflow transition | Responsibility intentionally transfers | Named new owner after the transfer condition |
| Shared execution | Several callers use one tool interface | Each caller checks its result in context |

A skill does not inherently supply isolation, a process boundary, or a typed
interface. Use those terms only when the actual host provides them. Plugin
dependencies describe package installation relationships; they do not replace
workflow contracts.

For consequential handoffs record the entry reason, required inputs/source
identity and assumptions, expected artifact and acceptance check, allowed
changes and inherited authorization, caller's remaining work, overall owner,
missing/failed/partial-result behavior, and return or transition condition.
Keep the brief proportional; do not invent a universal receipt schema.

Permit intentional review-and-revise cycles with a stable owner, explicit
progress condition, iteration bound, and stop rule. Flag accidental mutual
invocation and ambiguous completion. A child success cannot grant authority
for a parent workflow or turn an advisory suggestion into a transition.

Example: an architecture workflow passes a skill editor one approved resource
correction and preserved output contract. The editor returns changed paths and
checks. The architecture workflow still verifies all consumers, packaging,
and the overall result. Neither step installs or publishes the plugin merely
because the source edit succeeded.

## Follow reverse dependencies

Start at the actual changed rule, file, trigger, interface, or package boundary.
Search links, invocations, path construction, and artifact readers/writers;
read the matching consumers. Do not assume every skill is affected or that a
text search alone proves a complete dependency map.

| Change | Inspect | Selected evidence |
|---|---|---|
| Shared policy/reference | Loaders and governed workflows | Source comparison and affected stop/behavior case |
| Schema/template | Producers, readers, validators, handoffs | Required outputs and representative consuming workflow |
| Shared helper | All callers and argument/result assumptions | Existing deterministic tests and affected caller |
| Trigger/posture | Metadata, menu, neighbors, host adapters | Natural task and near miss in fresh context |
| Rename/removal | Links, invocations, catalog, manifests, examples | Consumer search, static gate, discovery |
| Extraction/relocation | Original gate, new load condition, installed path | Preserved contract and observed loading |
| Package boundary | Distribution rules, shared paths, source resolution | Inclusion and loaded-source identity |

Before an authorized restructure, capture inputs, required outputs, source
assumptions, permitted mutations, approval/stop rules, completion owners, and
existing verification. Compare the final state against those obligations.
Label deliberate behavior changes and their authorizing decision instead of
presenting them as mechanical moves.

Change an owner and its consumers coherently. Recheck actual callers before
removing an old path. Select materially different consumer paths for shared
changes; a local reference clarification needs less evidence than a global
resolver change. Missing runtime evidence stays unknown/inconclusive rather
than becoming a static pass. Keep temporary audit maps and migration notes in
the repository's established local review space, not a mandatory registry.
