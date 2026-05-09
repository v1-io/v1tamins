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
│   ├── plugins/marketplace.json  # Codex marketplace manifest
│   └── skills/                   # Canonical shared skills (source of truth)
├── .claude-plugin/
│   └── marketplace.json          # Claude Code marketplace manifest
├── plugins/
│   └── v1tamins/                 # Plugin package with generated v1-* skill mirrors
│       ├── .claude-plugin/plugin.json  # Claude Code plugin manifest
│       ├── .codex-plugin/plugin.json   # Codex plugin manifest
│       └── skills/                     # Shared skills consumed by both runtimes
└── scripts/
    └── sync-skill-hosts.sh       # Validates skill frontmatter and refreshes plugin mirrors
```

## Installation

v1tamins ships as a plugin for Claude Code and Codex. The same package serves both runtimes through sibling per-runtime manifests (`plugins/v1tamins/.claude-plugin/plugin.json` and `plugins/v1tamins/.codex-plugin/plugin.json`) reading from one shared `plugins/v1tamins/skills/` directory. Plugin skills use the `v1-` prefix to avoid collisions with other public or personal skills.

- Claude Code: `/plugin marketplace add v1-io/v1tamins` then `/plugin install v1tamins@v1tamins`
- Codex: `codex plugin marketplace add v1-io/v1tamins` then install via Codex's plugin UI

For local development against a checkout, use `~/v1tamins` in place of `v1-io/v1tamins`.

## Key Concepts

### Skills (.agents/skills/)

Portable shared skills live in `.agents/skills/`. Each skill is a directory containing a `SKILL.md` file with:

- YAML frontmatter: `name`, `description` (required); `allowed-tools` (recommended)
- Markdown body: usage syntax, workflow steps, examples

Codex-specific UI metadata lives in `agents/openai.yaml` when needed.

The generated plugin mirrors live in `plugins/v1tamins/skills/v1-<skill-name>/` and serve both the Claude Code and Codex plugin manifests. Do not edit those mirrors directly; edit `.agents/skills/<skill-name>/` and run `scripts/sync-skill-hosts.sh --write`.

Skill names use the canonical form (e.g. `pr`, `debug`) in `.agents/skills/`. Plugin-distributed skills use prefixed names (`v1-pr`, `v1-debug`) in both Claude Code and Codex.

Skills prefixed with `_` (e.g. `_grafana-dashboards`) are gitignored — they exist locally but are not distributed.

## Contributing Skills

1. Create `.agents/skills/<skill-name>/SKILL.md`
2. Add `agents/openai.yaml` when the skill should appear cleanly in Codex skill lists
3. Add YAML frontmatter with `name` and `description`. `allowed-tools` is recommended when the skill needs tool restrictions
4. Document usage, workflow steps, and examples
5. Run `scripts/sync-skill-hosts.sh --write` after creating, renaming, or changing skills
6. Run `scripts/sync-skill-hosts.sh` before committing
7. Test in a project before committing
8. Push to share with team

When updating shared docs, keep `AGENTS.md`, `CLAUDE.md`, and `README.md` aligned.

Before publishing shared skills or instructions, run a privacy and portability scan over the changed files. Review hits for private URLs, absolute paths, secrets, tokens, customer names, project-specific facts, and OS-specific commands that should be generalized.

## Architecture Notes

- **Plugin-only distribution**: `plugins/v1tamins/` packages generated `v1-*` skill mirrors and ships both a Claude Code plugin (`.claude-plugin/plugin.json`) and a Codex plugin (`.codex-plugin/plugin.json`) from one shared `skills/` directory
- **Project-agnostic**: Skills work across different project types without modification
- **Single source of truth**: All skill content lives in `.agents/skills/`; plugin mirrors are generated by `scripts/sync-skill-hosts.sh --write` and should never be hand-edited
