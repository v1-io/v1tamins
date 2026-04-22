# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**v1tamins** is a shared collection of AI development tools for the Version1 team. It provides skills, hooks, commands, rules, and MCP server configurations that are symlinked into developers' personal tool configurations (`~/.agents/`, `~/.claude/`, and `~/.cursor/`).

This is a **configuration distribution repository**, not an application. It contains no build system or tests - quality is maintained through git review, lightweight validation scripts, and usage feedback.

## Repository Structure

```
v1tamins/
├── .agents/
│   └── skills/          # Canonical shared skills for Codex and other agent runtimes
├── claude/
│   ├── skills/          # Claude-compatible entries, symlinked or mirrored from .agents/skills
│   └── hooks/           # Post-execution hooks (format.sh auto-formats Python/TS/JS)
├── cursor/
│   ├── commands/        # Cursor slash commands (markdown files)
│   └── rules/           # Generic development rules (.mdc files)
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
# Clone and install (creates symlinks to ~/.agents/, ~/.claude/, and ~/.cursor/)
git clone git@github.com:v1-io/v1tamins.git ~/v1tamins
~/v1tamins/install.sh

# Update
cd ~/v1tamins && git pull
```

The install script symlinks shared agent skills, Claude directories, and Cursor directories rather than copying files, so all developers share the same source of truth and updates propagate via `git pull`.

## Key Concepts

### Skills (.agents/skills/)
Portable shared skills live in `.agents/skills/`. Each skill is a directory containing a `SKILL.md` file with:
- YAML frontmatter: `name`, `description`, `allowed-tools`
- Markdown body: usage syntax, workflow steps, examples

Codex-specific UI metadata lives in `agents/openai.yaml` when needed. Claude Code compatibility entries live in `claude/skills/` and should symlink or mirror the shared skill rather than diverging from it.

Skills are invoked via `/skill-name` in Claude Code and via Codex skill discovery in agent runtimes.

### Hooks (claude/hooks/)
`format.sh` runs as a PostToolUse hook, auto-formatting:
- Python files with `black`
- TypeScript/JavaScript files with `prettier`

Enable debug logging: `CLAUDE_FORMAT_DEBUG=1`

### Cursor Rules (cursor/rules/)
`.mdc` files containing glob patterns and rules that apply context-aware guidance.
- `development.mdc` - Code quality, AI comment conventions (`AIDEV-NOTE:`, `AIDEV-TODO:`), logging standards

Note: Project-specific rules (backend patterns, frontend patterns, etc.) should live in individual project repositories.

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
6. Run `scripts/sync-skill-hosts.sh --write` after creating or renaming skills
7. Run `scripts/sync-skill-hosts.sh` before committing
8. Test in a project before committing
9. Push to share with team

## Architecture Notes

- **Symlink distribution**: Changes to v1tamins propagate to all users via `git pull`
- **Project-agnostic**: Skills/rules work across different project types without modification
- **Multi-tool unification**: Same capabilities available in Claude Code (skills), Cursor (commands), and Codex (skills)
