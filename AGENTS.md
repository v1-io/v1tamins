# AGENTS.md

This file provides guidance to Codex when working with code in this repository.

## Project Overview

**v1tamins** is a public-facing shared collection of reusable AI development skills, distributed as a plugin for Claude Code and Codex.

This is a **configuration distribution repository**, not an application. It has
no application build system or conventional test suite; quality is maintained
through the static plugin validator, committed routing fixtures, bounded
behavior evals, git review, and usage feedback.

## Public-Safe Requirement

Assume every committed file in this repository may be read outside the original private project context. Keep guidance generalizable and remove private or project-specific details before committing.

Do not add secrets, tokens, account IDs, private customer or project names, internal URLs, Slack channels, dashboard links, trace URLs, ticket URLs, production incident IDs, proprietary timelines, absolute local paths, or instructions that only make sense inside one private repository.

When extracting a private project lesson into v1tamins, keep the reusable workflow, failure mode, validation pattern, or decision rule. Replace private facts with placeholders such as `<repo>`, `<service>`, `<org-id>`, `<ticket>`, or `<incident-id>`. If the guidance cannot be generalized without losing its value, keep it in that project's local instructions instead of this repo.

## Repository Structure

```
v1tamins/
├── .agents/
│   └── plugins/marketplace.json  # Codex marketplace manifest
├── .claude-plugin/
│   └── marketplace.json          # Claude Code marketplace manifest
├── plugins/
│   └── v1tamins/                 # Plugin package and canonical skill source
│       ├── .claude-plugin/plugin.json  # Claude Code plugin manifest
│       ├── .codex-plugin/plugin.json   # Codex plugin manifest
│       └── skills/                     # Canonical v1-* skills consumed by both runtimes
└── scripts/
    ├── validate-plugin.sh        # Validates plugin manifests and skill frontmatter
    └── sync-skill-hosts.sh       # Legacy compatibility shim
```

## Installation

v1tamins ships as a plugin for Claude Code and Codex. The same package serves both runtimes through sibling per-runtime manifests (`plugins/v1tamins/.claude-plugin/plugin.json` and `plugins/v1tamins/.codex-plugin/plugin.json`) reading from one shared `plugins/v1tamins/skills/` directory. Plugin skills use the `v1-` prefix to avoid collisions with other public or personal skills.

- Claude Code: `/plugin marketplace add v1-io/v1tamins` then `/plugin install v1tamins@v1tamins`
- Codex: `codex plugin marketplace add v1-io/v1tamins` then install via Codex's plugin UI

For local development against a checkout, use `~/v1tamins` in place of `v1-io/v1tamins`.

## Key Concepts

### Skills (plugins/v1tamins/skills/)

Portable shared skills live in `plugins/v1tamins/skills/v1-<skill-name>/`. This plugin package is the source of truth. Each skill is a directory containing a `SKILL.md` file with:

- YAML frontmatter: `name`, `description` (required); `allowed-tools` (recommended)
- Markdown body: usage syntax, workflow steps, examples

Codex-specific UI metadata lives in `agents/openai.yaml` when needed.

Skill names use the `v1-` prefix in both directory names and frontmatter names (for example `v1-pr`, `v1-debug`) to avoid collisions with other public or personal skills.

Private plugin skill directories named `v1-_*` are gitignored — they can exist locally but are not distributed.

### Invocation taxonomy and description contract

Every distributed skill declares one `policy.invocation_posture` in its
`agents/openai.yaml` metadata:

- `implicit`: model-selectable and directly invocable for ordinary local work.
- `selective_implicit`: model-selectable and directly invocable, but costly,
  high-impact, or separately gated when it reaches an external or peer system.
- `explicit_only`: callable only from a human or explicitly named automation;
  set `allow_implicit_invocation: false` and
  `disable-model-invocation: true`.

This package has no supported `agent-only` posture. Keep orchestration entry
points such as `v1-implement-unit`, `v1-review-board`, `v1-pr`, and `v1-land-pr`
explicit even when their child skills are model-selectable. Child routing must
not open the parent workflow.

`SKILL.md` frontmatter descriptions are always-loaded routing metadata, not
miniature manuals. Keep each non-empty description to the skill's core purpose
plus distinct natural trigger phrases; target 180 characters or fewer. Keep
methods, outputs, edge cases, and routing boundaries in the body or a directly
linked reference. Update the trigger inventory and routing fixture whenever
this contract changes.

### General Skill Workflow

Use `v1-skilling-it` to create, edit, audit, or validate an Agent Skill and to
resolve whether its authoritative Canonical Source belongs in a personal
workspace, a project, a durable managed source, or a shared plugin. The
contribution steps below apply only when that Canonical Source is this v1tamins
repository.

### Autonomous Routing Evals

Skill metadata is runtime behavior. Codex and Claude Code select skills from
compact listings before loading the full skill body, and those listings can
shorten descriptions when many skills are installed.

Use `plugins/v1tamins/evals/trigger-inventory.md` to review whether a skill's
trigger contract is right, too broad, too narrow, or side-effectful. Use
`plugins/v1tamins/evals/skill-routing.jsonl` for should-trigger,
should-not-trigger, overlap, side-effect, and budget-stress cases. Any change to
a skill description, invocation policy, `agents/openai.yaml`, or routing-relevant
body guidance should update these eval files in the same diff.

For routing-sensitive changes, `scripts/run-skill-routing-live-eval.py` can run
an opt-in live Codex or Claude Code smoke sample. It may require local runtime
auth and writes ignored artifacts under `.v1tamins/live-routing/`; do not commit
raw transcripts.

To compare one installed Codex or Claude plugin root with the canonical plugin
package without mutating caches or credentials, run
`scripts/verify-installed-plugin.sh --canonical <plugin-root> --installed <plugin-root> --runtime <codex|claude>`.
Add `--probe-catalog` only when you want a read-only installed
`peer_catalog.py` probe after the install hash already matches; bytecode writes
are disabled for that probe, and stale installs skip the probe instead of
executing installed code.

## Migration Note

The canonical source moved from `.agents/skills/<skill-name>/` to `plugins/v1tamins/skills/v1-<skill-name>/`. Direct checkout consumers should update symlinks, scripts, and docs to use the plugin path and installed `v1-*` names. Marketplace/plugin consumers already using `/v1-*` skill names should not need to change anything.

## Contributing Skills

Before proposing a new skill, check `.out-of-scope/` for a prior rejection of the concept.

1. Create `plugins/v1tamins/skills/v1-<skill-name>/SKILL.md`
2. Add required `agents/openai.yaml` Codex metadata. Include `policy.invocation_posture` and `policy.side_effects` when a skill can publish externally, push to git remotes, launch peer agents, or record browser proof. Use `invocation_posture: explicit_only` with `disable-model-invocation: true` in `SKILL.md` for deliberate rituals and for invocations that can automatically perform outward side effects. Use `selective_implicit` with `allow_implicit_invocation: true` for high-recall workflows whose outward mutations remain separately explicit and user-gated; `policy.side_effects` is still required.
3. Add YAML frontmatter with `name` and `description`; `name` must match the `v1-*` directory. `allowed-tools` is recommended when the skill needs tool restrictions
4. Update `plugins/v1tamins/evals/trigger-inventory.md` and `plugins/v1tamins/evals/skill-routing.jsonl` with the intended trigger and near-miss behavior. Update `v1-menu` when a skill is added, renamed, removed, or changes invocation posture
5. Document usage, workflow steps, and examples
6. Add a changeset (`npx changeset`) describing the change. CI generates the version bump and `CHANGELOG.md` and keeps `package.json` and both plugin manifests in lockstep — don't hand-edit versions.
7. Run `scripts/validate-plugin.sh --verbose` before committing
8. Test in a project before committing
9. Push to share with team

When updating shared docs, keep `AGENTS.md`, `CLAUDE.md`, and `README.md` aligned.

Before publishing shared skills or instructions, run a privacy and portability scan over the changed files. Review hits for private URLs, absolute paths, secrets, tokens, customer names, project-specific facts, and OS-specific commands that should be generalized.

## Architecture Notes

- **Plugin-only distribution**: `plugins/v1tamins/` ships both a Claude Code plugin (`.claude-plugin/plugin.json`) and a Codex plugin (`.codex-plugin/plugin.json`) from one shared `skills/` directory
- **Project-agnostic**: Skills work across different project types without modification
- **Single source of truth**: All skill content lives in `plugins/v1tamins/skills/`; there is no tracked `.agents/skills` mirror

## Agent skills

### Issue tracker

Work is tracked in Linear, workspace `v1io`, team `VER`. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical triage vocabulary and its Linear workflow-state mapping. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context repository. Read `context.md` and relevant ADRs under
`docs/adr/`. See `docs/agents/domain.md`.
