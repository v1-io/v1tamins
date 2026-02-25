# Brainstorm: prove-work -- Visual Proof Artifacts for PRs

**Date:** 2026-02-24
**Status:** Brainstorm complete, ready for planning

## What We're Building

A Claude Code skill called `prove-work` that generates animated GIF artifacts showing the result of work done during a Claude Code session. The GIF gets uploaded as a GitHub asset and embedded directly in the PR description as visual proof of the change.

**Inspired by:** [Cursor's cloud agent computer use](https://cursor.com/blog/agent-computer-use) -- where agents record themselves interacting with software in VMs and attach video proof to PRs.

### How It Works

1. Claude drives a browser via Playwright MCP (navigate, click, fill forms, scroll) -- choosing what to demonstrate based on the task context
2. Underneath, a video recording captures the full browser session smoothly (not frame-by-frame screenshots)
3. A Python script converts the video to an optimized GIF
4. The GIF is uploaded as a GitHub asset and embedded in the PR body

### Two Trigger Modes

- **Manual:** User invokes `/prove-work` after completing a task. Claude infers what to demonstrate from the conversation context, launches browser, records interaction, produces GIF.
- **PR integration:** When Claude is about to create a PR (either via the pr-description skill or organically), it automatically runs the prove-work flow and embeds the artifact in the PR description.

## Why This Approach (Hybrid: Claude Drives + Script Records)

We evaluated three approaches:

| Approach | Quality | Agent intelligence | Complexity |
|---|---|---|---|
| **A: Pure MCP screenshots + Pillow stitch** | Frame-by-frame, choppy | Claude drives via MCP | Low |
| **B: Python Playwright script** | Smooth native video | Script drives (no agent reasoning) | Medium |
| **C: Hybrid (chosen)** | Smooth video | Claude drives via MCP | Higher |

**We chose C because:**

- The most valuable part is Claude's reasoning about *what* to demonstrate. Only MCP orchestration gives you that.
- Frame-by-frame GIFs (Approach A) look choppy and amateur for PR proof.
- A script-driven demo (Approach B) can't intelligently pick what to show based on task context.
- The complexity tradeoff is worth it -- the recording infrastructure is a one-time build.

## Key Decisions

1. **Output format:** Animated GIF. Renders inline in GitHub PR descriptions, no player needed, lightweight.
2. **Capture mechanism:** Playwright (headless, default) with claude-in-chrome as optional fallback for authenticated pages.
3. **Agent drives the demo:** Claude decides what URL to navigate to and what interactions to perform based on the task context. No user-provided scripts needed.
4. **Delivery:** Upload GIF as GitHub asset via `gh` CLI, embed URL in PR description markdown.
5. **Trigger:** Manual `/prove-work` invocation + automatic integration into PR creation workflow.
6. **Skill pattern:** Follow md2docs convention -- `SKILL.md` with `scripts/` directory containing Python tooling for video-to-GIF conversion.

## Architecture Sketch

```
claude/skills/prove-work/
  SKILL.md              # Skill definition, workflow instructions for Claude
  scripts/
    video_to_gif.py     # Convert Playwright video (.webm) to optimized GIF
    upload_gh_asset.py   # Upload GIF to GitHub and return embed URL (or use gh CLI directly)
```

### Recording Flow

```
1. Claude starts Playwright browser session with video recording enabled
   (Playwright MCP or Python playwright with page.video config)
2. Claude navigates to relevant URL, performs interactions via MCP tools
   (browser_navigate, browser_click, browser_fill_form, etc.)
3. Claude stops recording, video saved as .webm
4. scripts/video_to_gif.py converts .webm -> optimized .gif
   (using ffmpeg if available, imageio/moviepy as fallback)
5. GIF uploaded to GitHub as PR asset or saved locally
```

### Key Technical Questions to Resolve in Planning

- **Playwright MCP video recording:** Does the Playwright MCP server expose video recording start/stop controls? If not, we may need to use Python Playwright directly for the recording layer while Claude still drives via MCP for interaction. This is the critical technical risk.
- **ffmpeg availability:** ffmpeg produces far better GIFs than pure-Python solutions. Should the script auto-install via `brew install ffmpeg` on first run, or should we require it as a prereq?
- **GIF size limits:** GitHub has asset size limits. Need to define max duration, resolution, and frame rate to keep GIFs under ~10MB.
- **Dev server coordination:** For frontend changes, the local dev server needs to be running. Should the skill start it, or assume it's already running?

## Scope

### V1 (Build First)
- Manual `/prove-work` invocation
- Playwright-based browser recording
- Python script for video-to-GIF conversion
- Local file output (save to `/tmp/prove-work/`)
- Basic `gh` CLI upload to GitHub

### V2 (Iterate)
- Auto-trigger during PR creation
- Claude-in-chrome fallback for authenticated pages
- Smart dev server detection and auto-start
- GIF optimization (palette, dithering, frame reduction)
- Configurable recording duration and resolution

## Open Questions

1. Can Playwright MCP's browser session be configured for video recording, or do we need a separate Python Playwright process for the recording layer?
2. Should GIFs be committed to the repo (in `.artifacts/`) or only uploaded to GitHub as ephemeral assets?
3. How do we handle multi-page flows that require authentication?
4. What's the right default GIF duration cap? 10 seconds? 15?
