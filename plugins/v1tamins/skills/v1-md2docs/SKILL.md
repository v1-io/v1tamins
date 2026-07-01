---
name: v1-md2docs
description: Use when the user explicitly wants a Markdown file converted into a formatted Google Doc. Triggers on "turn this .md into a Google Doc", "publish this markdown as a doc", "md2docs".
disable-model-invocation: true
allowed-tools:
  - Bash
---
# md2docs

Convert a Markdown file to a formatted Google Doc with one command.

## Usage

Typical invocations:
- Claude Code: `/v1-md2docs path/to/file.md`
- Codex: invoke `v1-md2docs` from the skills menu or use `$v1-md2docs path/to/file.md`

Optional arguments after the file path:
- `--title "Custom Title"` to override the doc title (default: filename as title case)
- `--no-open` to skip opening the browser

## Workflow

1. Resolve the markdown file path from the user input.
2. Run the conversion script from the skill root:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

for dir in \
  "$REPO_ROOT/plugins/v1tamins/skills/v1-md2docs" \
  "${CLAUDE_PLUGIN_ROOT:-}" \
  "$HOME/.codex/skills/v1-md2docs" \
  "$HOME/.claude/skills/v1-md2docs"; do
  [ -n "$dir" ] && [ -f "$dir/scripts/md2docs.py" ] && SKILL_ROOT="$dir" && break
done

if [ -z "${SKILL_ROOT:-}" ]; then
  echo "ERROR: Could not find scripts/md2docs.py" >&2
  exit 1
fi

python3 "$SKILL_ROOT/scripts/md2docs.py" <file_path> [--title "Title"] [--no-open]
```

3. Report the Google Doc URL back to the user.

## First-Time Setup

If the script reports `No client_secret.json found`, guide the user through setup:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or use an existing one
3. Enable the **Google Drive API**
4. Go to **APIs & Services > Credentials**
5. Create an **OAuth 2.0 Client ID** with application type **Desktop app**
6. Download the JSON file
7. Save it to `~/.md2docs/client_secret.json`

The first run opens a browser for OAuth consent. After that, the token is cached at `~/.md2docs/token.json` and no browser auth is needed until the token expires.

Each developer authenticates with their own Google account. Docs are created in their personal Google Drive.

## What Gets Formatted

- H1-H6 headings with native Google Docs heading styles
- **Bold**, *italic*, and ***bold+italic***
- `inline code` with Courier New font and gray background
- Fenced code blocks with Courier New font, gray background, and border
- Tables with bordered cells and header row styling
- Unordered and ordered lists with proper nesting
- [Links](https://example.com) as clickable hyperlinks
- Horizontal rules
- Mermaid diagrams rendered as embedded images when `mmdc` or `npx` is available

## Environment Variables

- `MD2DOCS_CLIENT_SECRET` overrides the default `client_secret.json` path

## Dependencies

The script auto-installs these pip packages on first run if missing:
- `markdown`
- `google-auth`
- `google-auth-oauthlib`
- `google-api-python-client`

Optional for Mermaid diagram rendering:
- `mmdc` or `npx` with `@mermaid-js/mermaid-cli`
