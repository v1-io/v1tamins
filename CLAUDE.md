# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**v1tamins** is a shared collection of AI development tools for the Version1 team. It provides skills, hooks, commands, rules, and MCP server configurations that are linked into developers' personal tool configurations (`~/.claude/`, `~/.cursor/`, and `~/.codex/`).

This is a **configuration distribution repository**, not an application. It contains no build system or tests - quality is maintained through git review and usage feedback.

## Repository Structure

```
v1tamins/
├── claude/
│   ├── skills/          # Claude Code skills (SKILL.md files with YAML frontmatter)
│   └── hooks/           # Post-execution hooks (format.sh auto-formats Python/TS/JS)
├── cursor/
│   ├── commands/        # Cursor slash commands (markdown files)
│   └── rules/           # Generic development rules (.mdc files)
├── codex/
│   └── skills/          # Codex skills (SKILL.md files with YAML frontmatter)
├── mcp/
│   └── mcp.json         # MCP server configurations (Linear, LangSmith, Playwright, etc.)
├── templates/
│   └── CLAUDE.md.template  # Template for project-specific CLAUDE.md files
└── install.sh           # One-command setup script
```

## Installation

```bash
# Clone and install (links configs into ~/.claude/, ~/.cursor/, and ~/.codex/)
git clone git@github.com:v1-io/v1tamins.git ~/v1tamins
~/v1tamins/install.sh

# Update
cd ~/v1tamins && git pull
```

The install script symlinks Claude and Cursor directories, then symlinks Codex skills individually so existing personal Codex skills are preserved. This keeps v1tamins as the source of truth while letting updates propagate via `git pull`.

## Key Concepts

### Skills (claude/skills/)
Each skill is a directory containing a `SKILL.md` file with:
- YAML frontmatter: `name`, `description`, `allowed-tools`
- Markdown body: usage syntax, workflow steps, examples

Skills are invoked via `/skill-name` in Claude Code.

### Codex Skills (codex/skills/)
Codex skills use the same directory-per-skill shape with a `SKILL.md` file. The installer links each repo-owned Codex skill into `~/.codex/skills/` without replacing the whole directory.

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

1. Create `claude/skills/<skill-name>/SKILL.md` and, when relevant, `codex/skills/<skill-name>/SKILL.md`
2. Add YAML frontmatter with `name`, `description`, `allowed-tools`
3. Document usage, workflow steps, and examples
4. Test in a project before committing
5. Push to share with team

## Architecture Notes

- **Symlink distribution**: Changes to v1tamins propagate to all users via `git pull`
- **Project-agnostic**: Skills/rules work across different project types without modification
- **Multi-tool unification**: Same capabilities available in Claude Code (skills), Cursor (commands), and Codex (skills)
