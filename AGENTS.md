# AGENTS.md

This file provides guidance to Codex when working with code in this repository.

## Project Overview

**v1tamins** is a public-facing shared collection of reusable AI development skills, distributed as a plugin for Claude Code and Codex.

This is a **configuration distribution repository**, not an application. It contains no build system or tests — quality is maintained through git review, lightweight validation scripts, and usage feedback.

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

## Migration Note

The canonical source moved from `.agents/skills/<skill-name>/` to `plugins/v1tamins/skills/v1-<skill-name>/`. Direct checkout consumers should update symlinks, scripts, and docs to use the plugin path and installed `v1-*` names. Marketplace/plugin consumers already using `/v1-*` skill names should not need to change anything.

## Contributing Skills

1. Create `plugins/v1tamins/skills/v1-<skill-name>/SKILL.md`
2. Add `agents/openai.yaml` when the skill should appear cleanly in Codex skill lists
3. Add YAML frontmatter with `name` and `description`; `name` must match the `v1-*` directory. `allowed-tools` is recommended when the skill needs tool restrictions
4. Document usage, workflow steps, and examples
5. Bump both runtime plugin manifest versions when runtime plugin content changes: `plugins/v1tamins/.claude-plugin/plugin.json` and `plugins/v1tamins/.codex-plugin/plugin.json`.
6. Run `scripts/validate-plugin.sh` before committing
7. Test in a project before committing
8. Push to share with team

When updating shared docs, keep `AGENTS.md`, `CLAUDE.md`, and `README.md` aligned.

Before publishing shared skills or instructions, run a privacy and portability scan over the changed files. Review hits for private URLs, absolute paths, secrets, tokens, customer names, project-specific facts, and OS-specific commands that should be generalized.

## Architecture Notes

- **Plugin-only distribution**: `plugins/v1tamins/` ships both a Claude Code plugin (`.claude-plugin/plugin.json`) and a Codex plugin (`.codex-plugin/plugin.json`) from one shared `skills/` directory
- **Project-agnostic**: Skills work across different project types without modification
- **Single source of truth**: All skill content lives in `plugins/v1tamins/skills/`; there is no tracked `.agents/skills` mirror
