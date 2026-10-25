---
name: v1-md2docs
description: Use when explicitly converting a Markdown file into a formatted Google Doc. Triggers on "Markdown to Google Doc" or "publish this markdown as a doc".
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
   For a bare invocation, infer it only when exactly one Markdown file is clearly
   in scope in the conversation. Otherwise ask which file to convert; do not
   select the newest file or scan for an arbitrary candidate.
2. Confirm the selected file exists and is readable before environment setup.
   Reuse a suitable project-local Python virtual environment when available,
   or create the default below. Run dependency checks, installation, and
   conversion with that same interpreter from the skill root:

Run this shell block with Bash. If your tool defaults to zsh or another shell,
select Bash first; cache glob handling depends on it.

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RESOLVER=""
for candidate in \
  "$REPO_ROOT/plugins/v1tamins/scripts/resolve-skill-root.sh" \
  "${CLAUDE_PLUGIN_ROOT:-}/scripts/resolve-skill-root.sh" \
  "$HOME/.claude/skills/v1-md2docs/../../scripts/resolve-skill-root.sh" \
  "$HOME/.codex/skills/v1-md2docs/../../scripts/resolve-skill-root.sh" \
  "$HOME/.claude/plugins/cache"/*/v1tamins/*/scripts/resolve-skill-root.sh \
  "$HOME/.codex/plugins/cache/v1tamins/v1tamins"/*/scripts/resolve-skill-root.sh; do
  [ -x "$candidate" ] && RESOLVER="$candidate" && break
done
if [ -z "${RESOLVER:-}" ]; then
  echo "ERROR: Could not find resolve-skill-root.sh" >&2
  exit 1
fi
SKILL_ROOT="$("$RESOLVER" v1-md2docs scripts/md2docs.py)"

VENV_DIR="$REPO_ROOT/.venv/md2docs"
# Set VENV_DIR to the existing project-local environment when reusing one.
if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR" || exit 1
fi
PYTHON="$VENV_DIR/bin/python"
"$PYTHON" "$SKILL_ROOT/scripts/md2docs.py" <file_path> [--title "Title"] [--no-open]
```

   If dependencies are missing, install the reported packages into that same
   environment with `"$PYTHON" -m pip install markdown google-auth
   google-auth-oauthlib google-api-python-client`, then rerun the conversion.
   Record its absolute Python path and restore `PYTHON` to that exact path
   before installation or conversion in a fresh shell; rerun the resolver
   block as well to restore `SKILL_ROOT`.
   Do not install into the system interpreter or bypass an externally managed
   environment. If environment creation or installation fails, report it before
   attempting authentication or document creation.
3. Report the returned Google Doc URL after successful conversion. Do not
   repeat a document-creation request after an uncertain upload; reconcile the
   destination before another attempt.

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
- Mermaid diagrams rendered as embedded images when an installed `mmdc` succeeds;
  otherwise the diagram source remains a visible code block

## Environment Variables

- `MD2DOCS_CLIENT_SECRET` overrides the default `client_secret.json` path

## Dependencies

Install these packages in the isolated environment. The script reports missing
dependencies and exits before authentication; it never installs packages:
- `markdown`
- `google-auth`
- `google-auth-oauthlib`
- `google-api-python-client`

Mermaid image rendering is separate from the Python prerequisites. It uses
only an already installed `mmdc` executable from `@mermaid-js/mermaid-cli` on
`PATH`. The converter never invokes `npx` or fetches a Node package. If `mmdc`
is absent or rendering fails, it preserves the diagram as a visible code block.
Installing an optional renderer is a separate setup choice; it is not required
to create the document.
