# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**v1tamins** is a public-facing shared collection of reusable AI development tools. It provides skills, hooks, commands, rules, and MCP server configurations that are installed into developers' personal tool configurations (`~/.agents/`, `~/.claude/`, and `~/.cursor/`).

This is a **configuration distribution repository**, not an application. It contains no build system or tests - quality is maintained through git review, lightweight validation scripts, and usage feedback.

## Public-Safe Requirement

Assume every committed file in this repository may be read outside the original private project context. Keep guidance generalizable and remove private or project-specific details before committing.

Do not add secrets, tokens, account IDs, private customer or project names, internal URLs, Slack channels, dashboard links, trace URLs, ticket URLs, production incident IDs, proprietary timelines, absolute local paths, or instructions that only make sense inside one private repository.

When extracting a private project lesson into v1tamins, keep the reusable workflow, failure mode, validation pattern, or decision rule. Replace private facts with placeholders such as `<repo>`, `<service>`, `<org-id>`, `<ticket>`, or `<incident-id>`. If the guidance cannot be generalized without losing its value, keep it in that project's local instructions instead of this repo.

## Repository Structure

```
v1tamins/
├── .agents/
│   ├── plugins/marketplace.json  # Codex marketplace manifest
│   └── skills/          # Canonical shared skills for Codex and other agent runtimes
├── .claude-plugin/
│   └── marketplace.json  # Claude Code marketplace manifest
├── claude/
│   ├── skills/          # Claude-compatible entries, symlinked or mirrored from .agents/skills
│   └── hooks/           # Post-execution hooks (format.sh auto-formats Python/TS/JS)
├── cursor/
│   ├── commands/        # Cursor slash commands (markdown files)
│   └── rules/           # Generic development rules (.mdc files)
├── plugins/
│   └── v1tamins/        # Plugin package with generated v1-* skill mirrors
│       ├── .claude-plugin/plugin.json  # Claude Code plugin manifest
│       ├── .codex-plugin/plugin.json   # Codex plugin manifest
│       └── skills/                     # Shared skills consumed by both runtimes
├── .github/
│   └── copilot-instructions.md  # Repository-wide GitHub Copilot guidance
├── mcp/
│   └── mcp.json         # MCP server configurations (Linear, LangSmith, Playwright, etc.)
├── scripts/
│   └── sync-skill-hosts.sh  # Validates skill frontmatter, symlinks, and host metadata
├── templates/
│   └── CLAUDE.md.template  # Template for project-specific CLAUDE.md files
└── install.sh           # One-command setup script
```

## Installation

```bash
# Clone and install (creates managed entries in ~/.agents/, ~/.claude/, and ~/.cursor/)
git clone git@github.com:v1-io/v1tamins.git ~/v1tamins
~/v1tamins/install.sh

# Use copied agent skills for runtimes that reject symlink targets outside ~/.agents/skills
~/v1tamins/install.sh --copy-agent-skills

# Update
cd ~/v1tamins && git pull
```

Both Claude Code and Codex should prefer the plugin package in `plugins/v1tamins/`. The same package serves both runtimes through sibling per-runtime manifests (`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`) reading from one shared `skills/` directory; plugin skills use the `v1-` prefix to avoid collisions with other public or personal skills. The install script remains a compatibility adapter for shared agent installs, Claude hooks, Cursor commands/rules, and runtimes that do not consume plugin packages.

Plugin install commands:

- Claude Code: `/plugin marketplace add v1-io/v1tamins` then `/plugin install v1tamins@v1tamins`
- Codex: `codex plugin marketplace add v1-io/v1tamins` then install via Codex's plugin UI

The install script symlinks shared agent skills by default so updates propagate via `git pull`. Use `--copy-agent-skills` when a runtime rejects symlinks that resolve outside `~/.agents/skills`; rerun the installer after updates to refresh copied skills. The installer also removes legacy `~/.codex/skills` symlinks that point into the current checkout so Codex does not show duplicate v1tamins skills.

## Key Concepts

### Skills (.agents/skills/)
Portable shared skills live in `.agents/skills/`. Each skill is a directory containing a `SKILL.md` file with:
- YAML frontmatter: `name`, `description`, `allowed-tools`
- Markdown body: usage syntax, workflow steps, examples

Codex-specific UI metadata lives in `agents/openai.yaml` when needed. Claude Code compatibility entries live in `claude/skills/` and should symlink or mirror the shared skill rather than diverging from it.

The generated plugin mirrors live in `plugins/v1tamins/skills/v1-<skill-name>/` and serve both the Claude Code and Codex plugin manifests. Do not edit those mirrors directly; edit `.agents/skills/<skill-name>/` and run `scripts/sync-skill-hosts.sh --write`.

Legacy shared-agent skills keep ergonomic names such as `pr` and `debug`. Plugin-distributed skills use prefixed names such as `v1-pr` and `v1-debug` in both Claude Code and Codex.

### Hooks (claude/hooks/)
`format.sh` runs as a PostToolUse hook, auto-formatting:
- Python files with `black`
- TypeScript/JavaScript files with `prettier`

Enable debug logging: `CLAUDE_FORMAT_DEBUG=1`

### Cursor Rules (cursor/rules/)
`.mdc` files containing glob patterns and rules that apply context-aware guidance.
- `development.mdc` - Code quality, AI comment conventions (`AIDEV-NOTE:`, `AIDEV-TODO:`), logging standards

Note: Project-specific rules (backend patterns, frontend patterns, etc.) should live in individual project repositories.

### GitHub Copilot Instructions (.github/copilot-instructions.md)
Repository-wide GitHub Copilot guidance lives in `.github/copilot-instructions.md`. Keep it concise, broadly applicable, and aligned with `AGENTS.md`, `CLAUDE.md`, and the current repo structure. Do not duplicate long skill workflows there; link Copilot back to canonical surfaces such as `.agents/skills`, `scripts/sync-skill-hosts.sh`, and repo contribution rules.

### MCP Servers (mcp/mcp.json)
Configured integrations requiring environment variables:
- `LANGSMITH_API_KEY` - LLM observability
- `POSTMAN_API_KEY` - API testing
- `BRAVE_API_KEY` - Web search

## Contributing Skills

1. Create `.agents/skills/<skill-name>/SKILL.md`
2. Add `agents/openai.yaml` when the skill should appear cleanly in Codex skill lists
3. Add YAML frontmatter with `name`, `description`, `allowed-tools`
4. Document usage, workflow steps, and examples
5. If Claude compatibility is needed, mirror or symlink it into `claude/skills/<skill-name>/`
6. Run `scripts/sync-skill-hosts.sh --write` after creating, renaming, or changing skills
7. Run `scripts/sync-skill-hosts.sh` before committing
8. Test in a project before committing
9. Push to share with team

When updating `.github/copilot-instructions.md`, also check this file, `AGENTS.md`, and `README.md` so the documented host surfaces stay consistent.

Before publishing shared skills or instructions, run a privacy and portability scan over the changed files. Review hits for private URLs, absolute paths, secrets, tokens, customer names, project-specific facts, and OS-specific commands that should be generalized.

## Architecture Notes

- **Plugin-first dual distribution**: `plugins/v1tamins/` packages generated `v1-*` skill mirrors and ships both a Claude Code plugin (`.claude-plugin/plugin.json`) and a Codex plugin (`.codex-plugin/plugin.json`) from one shared `skills/` directory
- **Managed compatibility distribution**: Agent skills install as symlinks by default or copied directories for runtimes with symlink-escape restrictions
- **Project-agnostic**: Skills/rules work across different project types without modification
- **Multi-tool unification**: Same capabilities available in Claude Code (skills), Codex (skills), Cursor (commands/rules), and GitHub Copilot (repository instructions)
