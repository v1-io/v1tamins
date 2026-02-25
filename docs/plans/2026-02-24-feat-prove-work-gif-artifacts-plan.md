---
title: "feat: Add prove-work skill for GIF proof-of-work artifacts"
type: feat
date: 2026-02-24
---

# feat: Add prove-work skill for GIF proof-of-work artifacts

## Overview

A Claude Code skill that generates animated GIF artifacts showing the result of work done during a session and embeds them in GitHub PRs. Claude drives a browser to demonstrate the feature, records the session as video, converts to optimized GIF, uploads to GitHub, and embeds the URL in the PR description.

Inspired by [Cursor's cloud agent computer use](https://cursor.com/blog/agent-computer-use) where agents record themselves interacting with software and attach video proof to PRs.

## Problem Statement / Motivation

When Claude Code creates a PR, reviewers have no visual proof of what was built or fixed. They must check out the branch and run the app to verify UI changes. This creates:

- Slower review cycles for frontend/visual changes
- No persistent record of "what this looked like when it shipped"
- Missed regressions that a quick visual check would catch
- No parity with Cursor's agent video artifacts feature

## Proposed Solution

A skill called `prove-work` with two components:

1. **SKILL.md** -- Instructions for Claude to drive a browser demo based on conversation context
2. **scripts/video_to_gif.py** -- Python script to convert Playwright's .webm recording to an optimized GIF and upload to GitHub

### Architecture

```
claude/skills/prove-work/
  SKILL.md                        # Skill definition (< 500 lines)
  scripts/
    video_to_gif.py               # WebM -> GIF conversion + optimization + upload
  references/
    recording-patterns.md         # Patterns for what to record by change type
```

### Recording Flow

```
                                  ┌─────────────────────────────┐
                                  │  Claude: Analyze context     │
                                  │  - What changed?             │
                                  │  - What URL to navigate to?  │
                                  │  - What interactions to show?│
                                  └──────────┬──────────────────┘
                                             │
                                  ┌──────────▼──────────────────┐
                                  │  Start Playwright via Python │
                                  │  with record_video_dir       │
                                  │  (NOT MCP -- see rationale)  │
                                  └──────────┬──────────────────┘
                                             │
                                  ┌──────────▼──────────────────┐
                                  │  Claude generates + runs     │
                                  │  interaction script:          │
                                  │  - page.goto(url)            │
                                  │  - page.click(selector)      │
                                  │  - page.fill(field, value)   │
                                  │  - page.wait_for_timeout(ms) │
                                  └──────────┬──────────────────┘
                                             │
                                  ┌──────────▼──────────────────┐
                                  │  context.close() finalizes   │
                                  │  .webm in /tmp/prove-work/   │
                                  └──────────┬──────────────────┘
                                             │
                                  ┌──────────▼──────────────────┐
                                  │  video_to_gif.py:            │
                                  │  1. Decode .webm via pyav    │
                                  │  2. Quantize frames (Pillow) │
                                  │  3. Save as .gif             │
                                  │  4. Optimize via gifsicle    │
                                  │  5. Enforce 10MB limit       │
                                  │  6. Upload via gh CLI        │
                                  └──────────┬──────────────────┘
                                             │
                                  ┌──────────▼──────────────────┐
                                  │  Embed GIF URL in PR body    │
                                  │  (upsert ## Demo section)    │
                                  └─────────────────────────────┘
```

## Technical Approach

### Why Python Playwright (not Playwright MCP) for Recording

The brainstorm proposed using Playwright MCP with `--save-video`. After investigation:

- The `--save-video` flag on `@playwright/mcp` records the **entire MCP session**, not a targeted clip. It cannot be started/stopped per-skill.
- The flag's availability and behavior needs validation against `@playwright/mcp@latest`'s actual CLI.
- Even if it works, the global MCP config in `mcp/mcp.json` would need modification, affecting all users.
- A second MCP entry (`PlaywrightRecorder`) creates coordination complexity (which server is Claude talking to?).

**The cleaner approach:** Claude generates a self-contained Python Playwright script for each recording session. This gives:

- Full control over `record_video_dir` and `record_video_size`
- No global MCP config changes
- No coordination between MCP servers
- Claude's reasoning still drives what to demonstrate -- it writes the script based on context

The tradeoff is that Claude writes ~15-30 lines of interaction code per invocation instead of using MCP tools directly. This is acceptable because the interaction scripts are simple (navigate, click, wait, scroll) and Claude excels at generating them.

### SKILL.md Design

Following skilling-it conventions:

```yaml
---
name: prove-work
description: Use when generating visual proof-of-work GIFs for PRs, recording browser demos of completed features, or creating animated screenshots of UI changes. Triggers on "prove work", "record demo", "GIF for PR", "visual proof", "/prove-work".
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
---
```

**Workflow in SKILL.md:**

1. **Analyze context** -- Determine what changed and what to demonstrate
   - Read recent git diff to identify changed files
   - Infer the relevant URL (from routes, components, page names)
   - Identify key interactions to show (new button, form, page)
   - If nothing is visually demonstrable, tell the user and exit
2. **Check prerequisites** -- Verify dev server is running, dependencies installed
3. **Generate interaction script** -- Write a Python Playwright script to `/tmp/prove-work/interact.py`
4. **Execute recording** -- Run the interaction script (which records video)
5. **Convert to GIF** -- Run `video_to_gif.py` on the .webm output
6. **Upload and embed** -- If a PR exists, upload and embed; otherwise save locally

### scripts/video_to_gif.py

Single script handling conversion, optimization, and upload.

**Interface:**

```bash
python3 SKILL_DIR/scripts/video_to_gif.py \
  --input /tmp/prove-work/video.webm \
  --output /tmp/prove-work/demo.gif \
  --max-size-mb 10 \
  --fps 10 \
  --max-width 800 \
  --colors 128 \
  [--upload --repo owner/repo --pr 42]
```

**Dependencies (auto-installed on first run):**

```
pip install av pillow
```

System dependency (checked, not auto-installed):

```
brew install gifsicle
```

**Size enforcement strategy:**

```
1. Convert at default settings (10fps, 800px, 128 colors)
2. If > max_size_mb:
   a. Reduce colors to 64
   b. If still over: reduce fps to 8
   c. If still over: reduce max_width to 640
   d. If still over: truncate to first 10 seconds
   e. If still over: fail with error and suggest shorter recording
```

**GIF upload via `gh` CLI:**

```bash
# Ensure media-assets release exists (create if missing)
gh release view media-assets 2>/dev/null || \
  gh release create media-assets --title "Media Assets" --notes "GIF artifacts for PRs" --latest=false

# Upload with timestamped name to avoid collisions
gh release upload media-assets demo-pr42-20260224-143022.gif --clobber

# Get the download URL
gh release view media-assets --json assets \
  --jq '.assets[] | select(.name=="demo-pr42-20260224-143022.gif") | .browser_download_url'
```

**PR body embedding strategy:**

```
1. Read existing PR body via: gh pr view 42 --json body --jq .body
2. If body contains "## Demo" section: replace it
3. If body has no "## Demo" section: append it at the end
4. Update: gh pr edit 42 --body "$(new_body)"
```

The `## Demo` section format:

```markdown
## Demo

![Demo](https://github.com/owner/repo/releases/download/media-assets/demo-pr42-20260224-143022.gif)
```

### references/recording-patterns.md

Guidance for Claude on what to record based on change type:

| Change Type | What to Record |
|---|---|
| New page/route | Navigate to the page, scroll through it, interact with key elements |
| Form changes | Fill out the form, submit, show success/error state |
| Component changes | Navigate to page with component, interact with it, show before/after states |
| Styling changes | Navigate to affected pages, scroll to show the visual change |
| API/backend only | Show the API response in browser dev tools, or run a curl and show output |
| Bug fix | Reproduce the scenario that was broken, show it now works |
| Nothing visual | Tell the user: "This change has no visual component. Skipping proof-of-work." |

### Claude-Generated Interaction Script Template

Claude generates scripts like this based on context:

```python
"""Prove-work interaction script -- auto-generated by Claude"""
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

    # Navigate to the feature
    page.goto("http://localhost:3000/settings")
    page.wait_for_load_state("networkidle")
    time.sleep(1)  # Let the page settle for recording

    # Demonstrate the new feature
    page.get_by_label("Display name").fill("Carl McEncroe")
    time.sleep(0.5)
    page.get_by_role("button", name="Save").click()
    page.wait_for_selector("text=Settings saved")
    time.sleep(1)  # Hold on success state

    # Finalize
    context.close()
    browser.close()
```

### Path Resolution

Following the `last30days` skill pattern:

```bash
SKILL_DIR="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/prove-work}"
python3 "$SKILL_DIR/scripts/video_to_gif.py" --input /tmp/prove-work/*.webm --output /tmp/prove-work/demo.gif
```

### MCP Config Changes

**None for V1.** The skill uses Python Playwright directly, not the MCP server. The existing Playwright MCP entry in `mcp/mcp.json` is unaffected.

For V2 (claude-in-chrome fallback), we may add a `PlaywrightRecorder` MCP entry -- but this is deferred.

## Acceptance Criteria

### Functional Requirements

- [x] `/prove-work` triggers the skill and produces a GIF artifact
- [x] Claude correctly infers what to demonstrate from conversation context (git diff, recent files)
- [x] Playwright records a smooth .webm video of the browser interaction
- [x] `video_to_gif.py` converts .webm to optimized GIF under 10MB
- [x] GIF is uploaded to a `media-assets` GitHub release in the current repo
- [x] GIF URL is embedded in the current PR's `## Demo` section
- [x] If no PR exists, GIF is saved locally and path reported to user
- [x] If nothing is visually demonstrable, skill exits with a clear message
- [x] Dev server not running is detected and reported before recording

### Non-Functional Requirements

- [x] First-run dependency check: `playwright`, `av`, `Pillow` pip packages + `gifsicle` system binary
- [x] GIF file size stays under 10MB with progressive quality reduction
- [x] Asset names include PR number + timestamp to avoid collisions
- [x] Script path resolution works via `SKILL_DIR` pattern across installations
- [x] No changes to global MCP config required

### Quality Gates

- [x] SKILL.md under 500 lines, references used for detailed content
- [x] Passes skilling-it quality checklist (frontmatter, naming, description, imperative form)
- [x] `video_to_gif.py` handles errors explicitly (corrupt video, missing deps, upload failure)
- [ ] Tested with: new page, form change, bug fix, and backend-only scenarios

## Implementation Phases

### Phase 1: Core Recording + Conversion (V1)

**Files to create:**

- `claude/skills/prove-work/SKILL.md`
- `claude/skills/prove-work/scripts/video_to_gif.py`
- `claude/skills/prove-work/references/recording-patterns.md`

**Tasks:**

1. [x] Write `video_to_gif.py` with WebM-to-GIF conversion (pyav + Pillow + gifsicle)
2. [x] Add size enforcement (progressive quality reduction loop)
3. [x] Add `gh release upload` integration with media-assets release auto-creation
4. [x] Add PR body upsert logic (find/create `## Demo` section)
5. [x] Write `SKILL.md` with context analysis + interaction script generation workflow
6. [x] Write `recording-patterns.md` reference with change-type-to-demo mapping
7. [x] Test: record a simple page load, convert, upload, embed

### Phase 2: Polish + Edge Cases

1. Add dependency check at skill start (pip packages + gifsicle + playwright browsers)
2. Add dev server detection (check if localhost port is responding before recording)
3. Add `/tmp/prove-work/` cleanup (remove files older than 24 hours)
4. Add `--dry-run` support (record + convert but don't upload)
5. Add user confirmation before upload (show local GIF path, ask to proceed)
6. Handle private repos (warn that release assets may not be visible to external reviewers)

### Phase 3: PR Integration (V2)

1. Add explicit call from `pr-description` skill: "If prove-work skill is available, run it before finalizing PR"
2. Add claude-in-chrome fallback for authenticated pages
3. Add smart dev server start (detect framework, run appropriate start command)
4. Add viewport size detection from project config

## Dependencies & Risks

### Dependencies

| Dependency | Type | Install | Notes |
|---|---|---|---|
| `playwright` (Python) | pip | `pip install playwright && playwright install chromium` | First-run setup required |
| `av` (PyAV) | pip | `pip install av` | Bundles its own libav, no system ffmpeg needed |
| `Pillow` | pip | `pip install pillow` | GIF assembly and frame quantization |
| `gifsicle` | system | `brew install gifsicle` | GIF optimization. Not auto-installed -- checked and error reported if missing |
| `gh` CLI | system | Already installed (used by other skills) | GitHub release upload + PR editing |

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Claude generates wrong interaction script | Misleading proof artifact | recording-patterns.md guidance + user can re-run with explicit URL |
| Playwright browser install missing | Skill fails on first run | Dependency check step with clear install instructions |
| Dev server not running | Recording shows error page | Pre-flight check: HTTP request to target URL before recording |
| GIF still too large after all quality reductions | Upload fails | Final fallback: truncate to first N seconds, or fail with clear error |
| Private repo release assets not accessible | Broken image in PR | Warn user if repo is private; suggest alternative hosting |
| `gifsicle` not installed | GIF unoptimized, may exceed size limit | Check at start, provide install command, degrade gracefully (skip optimization) |

## References & Research

### Internal References

- Brainstorm: `docs/brainstorms/2026-02-24-prove-work-brainstorm.md`
- md2docs skill pattern: `claude/skills/md2docs/SKILL.md` -- script-based artifact generation
- e2e-testing skill: `claude/skills/e2e-testing/SKILL.md` -- Playwright patterns
- Executable code guide: `claude/skills/skilling-it/references/executable-code.md` -- script best practices
- Skill conventions: `claude/skills/skilling-it/SKILL.md` -- structure, naming, frontmatter

### External References

- [Cursor cloud agent computer use](https://cursor.com/blog/agent-computer-use) -- inspiration
- [Playwright Python video recording API](https://playwright.dev/python/docs/videos)
- [PyAV documentation](https://pyav.org/docs/stable/)
- [gifsicle optimization](https://github.com/kohler/gifsicle)
- [gh release upload](https://cli.github.com/manual/gh_release_upload)
- [@playwright/mcp](https://github.com/microsoft/playwright-mcp) -- MCP server (not used in V1 but referenced)
