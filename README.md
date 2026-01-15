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
├── claude/
│   ├── skills/          # 20 Claude Code skills
│   │   ├── code-review/
│   │   ├── pr-description/
│   │   ├── write-tests/
│   │   ├── fix-tests/
│   │   ├── deslop/
│   │   └── ...
│   └── hooks/           # Pre/post execution hooks
│       └── format.sh
├── cursor/
│   ├── commands/        # 22 Cursor slash commands
│   │   ├── code-review.md
│   │   ├── security-audit.md
│   │   ├── write-unit-tests.md
│   │   └── ...
│   └── rules/           # 6 Cursor rules
│       ├── backend-patterns.mdc
│       ├── frontend-patterns.mdc
│       └── ...
├── mcp/
│   └── mcp.json         # MCP server configurations
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

### Claude Code Skills & Hooks

Claude Code looks for skills in `~/.claude/skills/` and hooks in `~/.claude/hooks/`.

```bash
# Symlink skills directory
ln -sf ~/v1tamins/claude/skills ~/.claude/skills

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

## Skills Reference

| Skill | Description |
|-------|-------------|
| `code-review` | Thorough code review with actionable feedback |
| `pr-description` | Generate PR descriptions from commits |
| `write-tests` | Generate unit tests for code |
| `fix-tests` | Fix failing tests |
| `deslop` | Clean up AI-generated code slop |
| `refactor` | Refactor code for clarity |
| `complexity` | Analyze and reduce cognitive complexity |
| `changelog` | Generate changelogs from commits |
| `prd` | Product requirements document generation |
| `debug` | Systematic debugging workflow |
| `migrate` | Database/code migration assistance |
| `prompt-engineering` | Improve prompts |
| `address-review` | Address PR review comments |
| `analyze-tool-errors` | Debug tool execution errors |
| `file-organizer` | Organize project files |
| `interview-me` | Interview prep assistance |
| `rebuild` | Rebuild/regenerate code |
| `test-service` | Test service endpoints |

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
3. Commit your changes with a descriptive message:
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
- [Cursor](https://cursor.sh) IDE
- Node.js (for MCP servers)
- Python/uvx (for LangSmith MCP)
