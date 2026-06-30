---
name: v1-prove-work
description: Use when the user explicitly wants a browser demo GIF or visual proof for a completed UI change. Triggers on "prove work", "record demo", "GIF for PR", "visual proof", "proof of work", "/v1-prove-work".
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
---
# Prove Work

Generate an animated GIF showing the result of work done during a session and embed it in a GitHub PR.

## Quick Start

Typical invocations:
- Claude Code: `/v1-prove-work http://localhost:3000/settings --pr 42`
- Codex: invoke `v1-prove-work` from the skills menu or use `$v1-prove-work http://localhost:3000/settings --pr 42`

This records a browser interaction with `localhost:3000/settings`, converts the recording to a GIF, uploads it to GitHub, and embeds it in PR #42's `## Demo` section.

Without arguments, the skill infers the URL from the git diff and auto-detects the PR:

```text
/v1-prove-work
```

In Codex, the slash examples below map directly to `$v1-prove-work ...`.

## Usage

Typical invocations:
- Claude Code: `/v1-prove-work [url] [--pr NUMBER] [--no-upload]`
- Codex: invoke `v1-prove-work` from the skills menu or use `$v1-prove-work [url] [--pr NUMBER] [--no-upload]`

- `url` -- Override the target URL (default: inferred from context)
- `--pr NUMBER` -- PR number to embed the GIF into (default: auto-detected)
- `--no-upload` -- Save GIF locally without uploading to GitHub

## Workflow

### Step 1: Check Prerequisites

Run these checks before proceeding. Stop and report if any fail.

```bash
# Check Python playwright
python3 -c "import playwright" 2>/dev/null || pip install playwright

# Check playwright browsers
python3 -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.chromium.launch(headless=True).close(); p.stop()" 2>/dev/null || python3 -m playwright install chromium

# Check pyav and pillow (auto-installed by video_to_gif.py on first run)
python3 -c "import av; from PIL import Image" 2>/dev/null || echo "Dependencies will be auto-installed on first conversion."

# Check gifsicle (optional but recommended)
which gifsicle >/dev/null 2>&1 || echo "WARNING: gifsicle not found. Install with: brew install gifsicle"
```

### Step 2: Analyze Context

Determine what to demonstrate. Read the recent git diff to identify changed files:

```bash
git diff --name-only HEAD~1..HEAD 2>/dev/null || git diff --name-only --cached
```

**Decision tree:**

1. **User provided a URL** -> Use that URL directly
2. **Changed files include frontend code** (`.tsx`, `.jsx`, `.vue`, `.html`, `.css`, templates) -> Infer the route/page affected, construct localhost URL
3. **Changed files are backend only** (`.py`, `.rb`, `.go`, API routes with no views) -> Tell the user: "This change has no visual component. Skipping proof-of-work." and exit
4. **Changed files are config/infra** -> Same as above, exit with message
5. **Cannot determine URL** -> Ask the user for the URL

When inferring the URL, look for:
- Route definitions in the changed files
- Component/page names that map to routes
- Test files that reference specific URLs

Default base URL: `http://localhost:3000` (override if project uses a different port).

Verify the URL is reachable before recording:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ROUTE
```

If the server is not running (connection refused), tell the user:
> "Dev server is not running on localhost:3000. Start it and run the `v1-prove-work` skill again."

### Step 3: Generate Interaction Script

Write a Python Playwright script to `/tmp/prove-work/interact.py` that demonstrates the feature.

Read [references/recording-patterns.md](references/recording-patterns.md) for the script template, interaction patterns, and timing guidelines. Use the template from that file as the starting point -- fill in the interaction section based on context analysis.

### Step 4: Execute Recording

```bash
mkdir -p /tmp/prove-work
# Clean old recordings
rm -f /tmp/prove-work/*.webm /tmp/prove-work/*.gif

# Run the interaction script
python3 /tmp/prove-work/interact.py
```

If the script fails, read the error output. Common issues:
- **Selector not found** -> Take a screenshot first to inspect the page, then adjust selectors
- **Timeout** -> Increase `wait_for_load_state` timeout or check if the server is responding
- **Navigation error** -> Verify the URL is correct

### Step 5: Convert to GIF

Run the conversion script:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

for dir in \
  "$REPO_ROOT/plugins/v1tamins/skills/v1-prove-work" \
  "${CLAUDE_PLUGIN_ROOT:-}" \
  "$HOME/.codex/skills/v1-prove-work" \
  "$HOME/.claude/skills/v1-prove-work"; do
  [ -n "$dir" ] && [ -f "$dir/scripts/video_to_gif.py" ] && SKILL_DIR="$dir" && break
done

if [ -z "${SKILL_DIR:-}" ]; then
  echo "ERROR: Could not find scripts/video_to_gif.py" >&2
  exit 1
fi

python3 "$SKILL_DIR/scripts/video_to_gif.py" \
  --input /tmp/prove-work/ \
  --output /tmp/prove-work/demo.gif \
  --max-size-mb 10
```

The script:
1. Finds the most recent .webm in the input directory
2. Decodes frames via pyav at 10fps
3. Quantizes and assembles into GIF via Pillow
4. Optimizes with gifsicle (if available)
5. Progressively reduces quality if over 10MB

### Step 6: Upload and Embed

**If `--no-upload` was specified:** Report the local path and stop.

**Auto-detect PR number** (if not provided):

```bash
gh pr view --json number --jq .number 2>/dev/null
```

**If a PR exists**, upload and embed:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

for dir in \
  "$REPO_ROOT/plugins/v1tamins/skills/v1-prove-work" \
  "${CLAUDE_PLUGIN_ROOT:-}" \
  "$HOME/.codex/skills/v1-prove-work" \
  "$HOME/.claude/skills/v1-prove-work"; do
  [ -n "$dir" ] && [ -f "$dir/scripts/video_to_gif.py" ] && SKILL_DIR="$dir" && break
done

if [ -z "${SKILL_DIR:-}" ]; then
  echo "ERROR: Could not find scripts/video_to_gif.py" >&2
  exit 1
fi

python3 "$SKILL_DIR/scripts/video_to_gif.py" \
  --input /tmp/prove-work/ \
  --output /tmp/prove-work/demo.gif \
  --max-size-mb 10 \
  --upload \
  --pr PR_NUMBER
```

**If no PR exists**, save locally and report:

```
GIF saved to: /tmp/prove-work/demo.gif
No open PR found for this branch. Run the `v1-prove-work` skill again with `--pr NUMBER` after creating a PR, or use `--no-upload` to keep the GIF local.
```

### Step 7: Report Result

After completion, report:

```
Proof of work recorded!

  GIF: /tmp/prove-work/demo.gif (X.X MB)
  URL: https://github.com/owner/repo/releases/download/media-assets/demo-pr42-20260224-143022.gif
  PR:  #42 -- ## Demo section updated

Recorded: [brief description of what was demonstrated]
```

## Examples

**Example 1: New settings page**

```
Input:  /v1-prove-work
Diff:   app/pages/settings.tsx, app/api/settings.ts
Output:
  Proof of work recorded!
    GIF: /tmp/prove-work/demo.gif (1.8 MB)
    URL: https://github.com/acme/app/releases/download/media-assets/demo-pr12-20260224-091500.gif
    PR:  #12 -- ## Demo section updated
    Recorded: Navigated to /settings, filled display name, clicked Save, showed success toast
```

**Example 2: Explicit URL with PR number**

```
Input:  /v1-prove-work http://localhost:5173/dashboard --pr 27
Output:
  Proof of work recorded!
    GIF: /tmp/prove-work/demo.gif (2.4 MB)
    URL: https://github.com/acme/app/releases/download/media-assets/demo-pr27-20260224-143000.gif
    PR:  #27 -- ## Demo section updated
    Recorded: Navigated to /dashboard, scrolled through widgets, toggled dark mode
```

**Example 3: Backend-only change**

```
Input:  /v1-prove-work
Diff:   app/services/billing.py, tests/test_billing.py
Output: This change has no visual component. Skipping proof-of-work.
```

**Example 4: Local only**

```
Input:  /v1-prove-work --no-upload
Output:
  GIF saved to: /tmp/prove-work/demo.gif (1.1 MB)
```

## Error Handling

| Error | Action |
|---|---|
| Dev server not running | Report the error, suggest starting the server |
| Playwright not installed | Auto-install via pip + playwright install chromium |
| No .webm produced | Check interact.py output, report the error |
| GIF exceeds 10MB after all reductions | Report the size, suggest a shorter recording |
| gh CLI not authenticated | Report the error, suggest `gh auth login` |
| No visual changes detected | Tell the user, exit cleanly |

## Reference Files

- **[references/recording-patterns.md](references/recording-patterns.md)** -- What to record for each change type, interaction patterns, timing, script template
