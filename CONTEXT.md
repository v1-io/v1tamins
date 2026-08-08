# v1tamins Context

v1tamins is a public plugin package of reusable AI coding skills, distributed to
Claude Code and Codex from one shared source directory. It is a configuration
distribution repository, not an application: what ships is skill text, routing
metadata, and plugin manifests. Its central problem is not whether a skill reads
well, but whether a runtime picks the right skill at the right moment, from
compact metadata, without loading the full skill body first.

## Language

**Skill**
One directory under `plugins/v1tamins/skills/v1-<name>/` holding a `SKILL.md`
and its Codex metadata. It is the unit of distribution and the unit of review.
Each skill does one job; the leverage comes from chaining several of them.
_Avoid_: prompt, command, macro, agent, tool, plugin.

**Trigger**
A natural phrase in a skill's description that should make a runtime select that
skill. Triggers are written for the words a user actually types, not for the
skill's internal name. A trigger that also fires for a neighbouring skill is a
routing defect, not a nice-to-have.
_Avoid_: keyword, hotword, intent, tag.

**Description contract**
The rule governing `SKILL.md` frontmatter descriptions: they are always-loaded
routing metadata, not a miniature manual. A description carries the core purpose
plus distinct triggers and targets 180 characters or fewer. Methods, outputs,
and edge cases belong in the body or a linked reference.
_Avoid_: summary, blurb, docstring, skill description text.

**Invocation posture**
The single declared rule for how a skill may be reached: `implicit`,
`selective_implicit`, or `explicit_only`. It is declared once, in the skill's
`agents/openai.yaml`, and it decides whether a model may open the workflow on
its own. Skills with outward side effects stay explicit or gated.
_Avoid_: permission level, visibility, access mode, autonomy setting.

**Routing eval**
The committed evidence that routing still behaves: the trigger inventory and the
should-trigger / should-not-trigger / overlap / side-effect cases in
`plugins/v1tamins/evals/`. Any change to a name, description, posture, or
routing-relevant guidance updates the routing eval in the same diff.
_Avoid_: test suite, benchmark, regression tests, fixtures.

**Canonical Source**
The one authoritative home for a skill's content — a personal workspace, a
single project, a managed source, or this shared plugin. Deciding the Canonical
Source comes before writing the skill, because it decides who maintains it and
who can read it.
_Avoid_: master copy, upstream, origin, single source of truth.

**Plugin package**
`plugins/v1tamins/`, which serves both runtimes from one shared `skills/`
directory through sibling per-runtime manifests. There is no per-runtime copy of
a skill; a change lands once and reaches both.
_Avoid_: bundle, module, extension, distribution.

**Marketplace manifest**
The file a runtime reads to discover this package before any skill is installed
(`.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`).
Version numbers across the manifests and `package.json` move together, generated
from a changeset rather than hand-edited.
_Avoid_: registry file, catalog, index, package index.

**Public-safe**
The standing rule that every committed file may be read outside the private
project that inspired it. Reusable workflow, failure mode, and decision rule
stay; private names, internal URLs, absolute local paths, and secrets are
replaced with placeholders or the guidance stays in the private project.
_Avoid_: sanitized, scrubbed, redacted, cleaned, anonymized.
