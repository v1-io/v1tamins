# Architecture decisions

Use these judgments on the inspected workflow. They are design guidance, not
universal formatting tests. Discover the target's conventions rather than
imposing v1tamins names, metadata, release process, or rejected directions.

## Capability boundaries

A separate skill earns an entry point through a distinct user goal or trigger,
different inputs or success criteria, or independent reuse. Keep branches of
one job together when they share a completion owner. Supporting knowledge can
be a reference; a deterministic operation can be a script. A helper skill is
not a storage location for shared prose.

Compare discovery descriptions and actual workflows separately. Check both
overlap (two owners competing for one request) and gaps (every owner assumes
another does a required step). An architecture request concerns relationships
between components; an isolated authoring edit stays with the authoring owner
unless its actual effects cross that boundary.

## Content and loading

| Content | Preferred owner | Check |
|---|---|---|
| Operation, essential gates, completion | Entry point | Obligations are visible before optional loads |
| Substantial conditional method | Direct reference | Required load precedes its governed action |
| Shared meaning or procedure | Existing canonical owner | Consumers need the same meaning and should change together |
| Repeatable computation | Existing tool/helper | Determinism solves a demonstrated problem |
| Material copied into output | Asset/template | Consumer knows its format and purpose |
| Release/contributor process | Repository guidance | Installed workflows do not depend on absent maintainer files |

Moving an essential rule creates a loading dependency. Keep its gate in the
entry point or require the reference immediately before the governed action.
Do not copy a whole policy into every consumer for visibility. Line/word
budgets can guide authoring, but do not prove a structure reliable or defective.

## Shared resources and reachability

For each material shared resource identify its owner/purpose, actual consumers,
their load stage/condition, version assumptions, missing-resource behavior,
and affected checks. Similar prose does not establish identical contracts.
Preserve intentional domain or host variants that must evolve independently.

Prefer an existing skill's resource when its ownership remains clear. A
plugin-level shared location is justified only when no single skill owns it
and centralization removes actual ambiguity or coupled maintenance.

Keep these checks distinct:

1. **Source existence:** the exact required file exists and was read.
2. **Package inclusion:** the distributed boundary includes it, or a declared,
   available dependency supplies it. Resolve symlinks as well as lexical paths.
3. **Runtime reachability:** the intended host loads that file from the intended
   package revision. A filename, cache search result, or matching version is
   insufficient identity evidence.

Do not assume plugin-root instructions become skill context automatically.
Check documented host behavior before depending on it. A helper that searches
several installations locates candidates; it does not prove same-package
identity. A checkout-only fallback can conceal a broken distributed path.

An absent manifest is not a defect by itself. Establish the target host,
supported package mode, and documented required metadata before recommending
packaging additions. If those facts are unresolved or unavailable, report that
part as unassessed rather than inventing a host requirement.

Review executable callers as well as helpers: inputs, result interpretation,
dependencies, filesystem scope, errors, cleanup, and the scope a successful
receipt actually certifies. Keep architectural judgment in instructions;
extend a checker only for an objective invariant with concrete evidence.

## Worked decisions

- **Healthy sharing:** `draft` produces an outline and `review` checks it; both
  load one packaged output contract before their action. Each owns its result.
  Keep the shared contract and distinct goals. No new shared folder is needed.
- **Conflicting output owners:** two workflows require incompatible fields in
  the same handoff artifact. Read both rules and the actual consumer. Choose
  one canonical contract or explicit variants; update producer, consumer, and
  checker together. Similar wording alone is not a conflict.
- **Package gap:** a skill loads a root-level maintainer README that is omitted
  from the plugin. Put required runtime guidance inside the existing package
  owner and update the link; keep maintainer-only process at repository root.
- **Evidence gap:** an unavailable reference may conceal a mandatory gate.
  Report that branch as unsupported and continue independent mapping. Do not
  manufacture the reference or infer a defect from its filename.
