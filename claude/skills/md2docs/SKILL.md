---
name: md2docs
description: Convert a Markdown file into a nicely formatted Google Doc and open it in the browser. Use when the user wants to create a Google Doc from a .md file, share markdown content as a Google Doc, or invoke /md2docs. Handles headings, bold, italic, inline code, fenced code blocks, tables, lists, links, horizontal rules, and mermaid diagrams.
allowed-tools:
  - Bash
---

# md2docs

Convert a Markdown file to a formatted Google Doc with one command.

## Usage

```
/md2docs <path-to-file.md>
```

Optional arguments after the file path:
- `--title "Custom Title"` to override the doc title (default: filename as title case)
- `--no-open` to skip opening the browser

## Workflow

1. Read the markdown file specified by the user
2. Run the conversion script:

```bash
python3 SKILL_DIR/scripts/md2docs.py <file_path> [--title "Title"] [--no-open]
```

Replace `SKILL_DIR` with the absolute path to this skill's directory (the directory containing this SKILL.md file).

3. Report the Google Doc URL back to the user

## First-Time Setup

If the script reports "No client_secret.json found", guide the user through setup:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use existing)
3. Enable the **Google Drive API**
4. Go to **APIs & Services > Credentials**
5. Create an **OAuth 2.0 Client ID** (application type: **Desktop app**)
6. Download the JSON file
7. Save it to `~/.md2docs/client_secret.json`

The first run opens a browser for OAuth consent. After that, the token is cached at `~/.md2docs/token.json` and no browser auth is needed until the token expires.

Each developer authenticates with their own Google account. Docs are created in their personal Google Drive.

## What Gets Formatted

- H1-H6 headings with native Google Docs heading styles
- **Bold**, *italic*, ***bold+italic***
- `inline code` with Courier New font and gray background
- Fenced code blocks with Courier New font, gray background, and border
- Tables with bordered cells and header row styling
- Unordered and ordered lists with proper nesting
- [Links](https://example.com) as clickable hyperlinks
- Horizontal rules
- Mermaid diagrams rendered as embedded images (requires `mmdc` or `npx`)

## Environment Variables

- `MD2DOCS_CLIENT_SECRET` - override path to client_secret.json (default: `~/.md2docs/client_secret.json`)

## Dependencies

The script auto-installs these pip packages on first run if missing:
- `markdown`
- `google-auth`
- `google-auth-oauthlib`
- `google-api-python-client`

Optional for mermaid diagram rendering:
- `mmdc` (mermaid CLI) or `npx` (will use `@mermaid-js/mermaid-cli`)
