# v1tamins

```
██╗   ██╗  ██╗ ████████╗ █████╗ ███╗   ███╗██╗███╗   ██╗███████╗
██║   ██║ ███║ ╚══██╔══╝██╔══██╗████╗ ████║██║████╗  ██║██╔════╝
██║   ██║ ╚██║    ██║   ███████║██╔████╔██║██║██╔██╗ ██║███████╗
╚██╗ ██╔╝  ██║    ██║   ██╔══██║██║╚██╔╝██║██║██║╚██╗██║╚════██║
 ╚████╔╝   ██║    ██║   ██║  ██║██║ ╚═╝ ██║██║██║ ╚████║███████║
  ╚═══╝    ╚═╝    ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝
```

Daily supplements for healthy code. A shared collection of AI development tools from the Version1 team.

## What's Inside

```
v1tamins/
├── .agents/
│   └── skills/          # Canonical shared skills for Codex and other agent runtimes
│       ├── md2docs/
│       └── ...
├── claude/
│   ├── skills/          # Claude-compatible entries, symlinked or mirrored from .agents/skills
│   │   ├── code-review/
│   │   ├── pr-description/
│   │   ├── write-tests/
│   │   ├── fix-tests/
│   │   ├── deslop/
│   │   └── ...
│   └── hooks/           # Pre/post execution hooks
│       └── format.sh
├── cursor/
│   ├── commands/        # Cursor slash commands
│   │   ├── code-review.md
│   │   ├── security-audit.md
│   │   ├── write-unit-tests.md
│   │   └── ...
│   └── rules/           # Cursor rules
│       └── development.mdc
├── mcp/
│   └── mcp.json         # MCP server configurations
├── scripts/
│   └── sync-skill-hosts.sh  # Validate skill frontmatter and sync host metadata
└── templates/           # Reusable templates (CLAUDE.md, etc.)
```

## Quick Install

```bash
# Clone the repo
git clone git@github.com:v1-io/v1tamins.git ~/v1tamins

# Run the install script
~/v1tamins/install.sh
```

## Manual Setup

### Codex / Shared Agent Skills

The canonical repo path for portable skills is `.agents/skills/`.

For repo-managed installs, keep `~/.agents/skills/` as a real user-owned directory and symlink each v1tamins skill into it:

```bash
mkdir -p ~/.agents/skills
for skill in ~/v1tamins/.agents/skills/*; do
  ln -sfn "$skill" ~/.agents/skills/"$(basename "$skill")"
done
```

Do not symlink the whole `~/.agents/skills` directory to this repo. Public, vendor, and personal skills installed into global skill directories should remain outside v1tamins so they do not appear in `git status`.

For standalone user-global Codex installs outside this repo, Codex's default skill location is `~/.codex/skills/`.

### Claude Code Skills & Hooks

Claude Code looks for skills in `~/.claude/skills/` and hooks in `~/.claude/hooks/`. In this repo, `claude/skills/` is the Claude compatibility surface and may symlink back to `.agents/skills/`.

```bash
mkdir -p ~/.claude/skills
for skill in ~/v1tamins/claude/skills/*; do
  ln -sfn "$skill" ~/.claude/skills/"$(basename "$skill")"
done

# Symlink hooks directory
ln -sf ~/v1tamins/claude/hooks ~/.claude/hooks
```

### Cursor Commands & Rules

Cursor looks for commands in `~/.cursor/commands/` and rules in `~/.cursor/rules/`.

```bash
# Symlink commands directory
ln -sf ~/v1tamins/cursor/commands ~/.cursor/commands

# Symlink rules directory
ln -sf ~/v1tamins/cursor/rules ~/.cursor/rules
```

### MCP Servers

Copy or merge the MCP config into your Cursor config:

```bash
# Copy MCP config (overwrites existing)
cp ~/v1tamins/mcp/mcp.json ~/.cursor/mcp.json

# Or manually merge with existing config
```

**Configured MCP Servers:**
| Server | Type | Description |
|--------|------|-------------|
| Linear | SSE | Project management integration |
| LangSmith | stdio | LLM observability (requires `LANGSMITH_API_KEY`) |
| Postman | HTTP | API testing (requires `POSTMAN_API_KEY`) |
| Notion | stdio | Documentation integration |
| Playwright | stdio | Browser automation |
| context7 | HTTP | Documentation lookup |
| brave-search | stdio | Web search (requires `BRAVE_API_KEY`) |

## Claude/Codex Skills Reference

Portable shared skills should live in `.agents/skills/<skill-name>/` with:

- `SKILL.md` as the shared source of truth
- `agents/openai.yaml` for Codex UI metadata when needed
- optional `scripts/`, `references/`, and `assets/`

Claude-facing entries in `claude/skills/` should be thin mirrors or symlinks rather than hand-maintained forks.

The table lists runtime skill names from `SKILL.md` frontmatter. A few legacy directories are underscore-prefixed on disk, for example `.agents/skills/_file-organizer/`, but the skill name remains `file-organizer`.

| Skill | Description |
|-------|-------------|
| `address-review` | Address PR review comments |
| `autoresearch-skill` | Run autonomous optimization loops |
| `changelog` | Generate changelogs from commits |
| `code-review` | Thorough code review with actionable feedback |
| `complexity` | Analyze and reduce cognitive complexity |
| `debug` | Systematic debugging workflow |
| `deep-research` | Research and synthesize multi-source topics |
| `deslop` | Clean up AI-generated code slop |
| `docs-freshness` | Sync documentation with shipped changes |
| `e2e-testing` | Implement and debug browser tests |
| `file-organizer` | Organize project files |
| `fix-tests` | Fix failing tests |
| `game-changing-features` | Find high-leverage product opportunities |
| `grafana-dashboards` | Create Grafana dashboards |
| `interview-me` | Refine ideas through structured questioning |
| `land-pr` | Commit, push, open, monitor, and ready a PR through CI handoff |
| `learn-from-pr` | Extract lessons after PRs |
| `md2docs` | Convert Markdown into Google Docs |
| `pr` | Ship local work as a pull request |
| `pr-description` | Generate PR descriptions from commits |
| `prd` | Product requirements document generation |
| `prompt-engineering` | Improve prompts |
| `prompt-engineering-v1tamins` | Improve GPT-5.4/OpenRouter prompts |
| `prove-work` | Record visual proof of work |
| `python-performance-optimization` | Profile and optimize Python code |
| `refactor` | Refactor code for clarity |
| `skilling-it` | Create and refine shared agent skills |
| `stickify` | Make communications more memorable |
| `strategy-review` | Review plans for strategy, scope, and user value |
| `write-tests` | Generate unit tests for code |

## Cursor Commands Reference

| Command | Description |
|---------|-------------|
| `/code-review` | Review selected code |
| `/security-audit` | Security vulnerability scan |
| `/write-unit-tests` | Generate unit tests |
| `/fix-failing-tests` | Fix broken tests |
| `/deslop` | Remove AI slop from code |
| `/refactor-code` | Refactor for clarity |
| `/reduce-cognitive-complexity` | Simplify complex code |
| `/generate-pr-description` | Generate PR description |
| `/debug-issue` | Debug workflow |
| `/land-pr` | Commit, push, open, monitor, and ready a PR through CI handoff |
| `/optimize-performance` | Performance optimization |
| `/add-documentation` | Add code documentation |
| `/clean-logging` | Clean up logging statements |
| `/security-review` | Security-focused review |
| `/address-copilot-review` | Address Copilot review comments |
| `/frontend-design` | Frontend design guidance |
| `/write-prd-for-linear` | Generate PRD for Linear |

## Updating

Pull the latest changes and re-run install if needed:

```bash
cd ~/v1tamins && git pull
```

## Validation

Run the skill host sync check before committing skill changes:

```bash
scripts/sync-skill-hosts.sh
```

When creating or renaming a skill, let the script create missing Claude host symlinks:

```bash
scripts/sync-skill-hosts.sh --write
```

The check validates `SKILL.md` YAML frontmatter, optional `agents/openai.yaml` metadata, and the `claude/skills/` compatibility surface.
Use `--verbose` when you need the per-file trace.

## Contributing

We welcome contributions! Here's how to get started:

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone git@github.com:YOUR_USERNAME/v1tamins.git ~/v1tamins
   cd ~/v1tamins
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream git@github.com:v1-io/v1tamins.git
   ```

### Make Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/my-new-skill
   ```
2. Make your changes and test them in a project
3. If you created or renamed a skill, run `scripts/sync-skill-hosts.sh --write`
4. Run `scripts/sync-skill-hosts.sh`
5. Commit your changes with a descriptive message:
   ```bash
   git add .
   git commit -m "Add new skill: my-cool-skill"
   ```

### Open a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/my-new-skill
   ```
2. Go to the [v1tamins repository](https://github.com/v1-io/v1tamins) on GitHub
3. Click "Compare & pull request"
4. Fill in a clear title and description of your changes
5. Submit the pull request for review

### Keeping Your Fork Updated

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- [Codex](https://openai.com/codex/) CLI
- [Cursor](https://cursor.sh) IDE
- Node.js (for MCP servers)
- Python/uvx (for LangSmith MCP)
- Ruby (for YAML validation; no gems required)
