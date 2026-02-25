---
name: prove-work
description: Use when generating visual proof-of-work GIFs for PRs, recording browser demos of completed features, or creating animated artifacts of UI changes. Triggers on "prove work", "record demo", "GIF for PR", "visual proof", "proof of work", "/prove-work".
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
---

# Prove Work

Generate an animated GIF showing the result of work done during a session and embed it in a GitHub PR.

## Usage

```
/prove-work [url] [--pr NUMBER] [--no-upload]
```

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
> "Dev server is not running on localhost:3000. Start it and run /prove-work again."

### Step 3: Generate Interaction Script

Write a Python Playwright script to `/tmp/prove-work/interact.py` that demonstrates the feature.

Read [references/recording-patterns.md](references/recording-patterns.md) for guidance on:
- What to record for each change type
- Interaction patterns (scrolling, hovering, filling forms)
- Timing guidelines (pauses between actions, hold times)

**Script structure:**

```python
"""Prove-work interaction script -- auto-generated"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        record_video_dir="/tmp/prove-work/",
        record_video_size={"width": 1280, "height": 720},
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()

    # Navigate and wait for page to load
    page.goto("TARGET_URL")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # Demonstrate the feature
    # [Fill this section based on context analysis]

    # Hold on final state
    time.sleep(1.5)

    # Finalize recording
    context.close()
    browser.close()
```

**Guidelines for the interaction section:**
- Keep total recording under 15 seconds
- Add `time.sleep(0.3-0.5)` between actions for natural pacing
- Hover before clicking to show intent
- Wait for feedback after submitting forms
- Hold on the final state for 1.5-2 seconds
- Use role-based selectors when possible: `page.get_by_role()`, `page.get_by_label()`
- Fall back to text selectors: `page.get_by_text()`, `page.locator("text=...")`

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
SKILL_DIR="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/prove-work}"
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
SKILL_DIR="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/prove-work}"
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
No open PR found for this branch. Run /prove-work --pr NUMBER after creating a PR, or use --no-upload to keep the GIF local.
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
