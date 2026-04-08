The AI world reinvents itself every month. This skill keeps you current.

`/last30days` researches your topic across **Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, and the web** from the last 30 days, finds what the community is actually upvoting, sharing, betting on, and saying on camera, and writes you a grounded narrative with real citations.

## What's New in v2.9.1

**Auto-save to ~/Documents/Last30Days/.** Every run now saves the complete research briefing - synthesis, stats, and follow-up suggestions - as a topic-named `.md` file to your Documents folder. Build a personal research library without lifting a finger. Inspired by [@devin_explores](https://x.com/devin_explores) who was already doing this manually.

## Three Headline Features in v2.9

**1. ScrapeCreators Reddit as default.** One `SCRAPECREATORS_API_KEY` now covers Reddit, TikTok, and Instagram - three sources, one key. No more `OPENAI_API_KEY` required for Reddit search. Faster, more reliable, and simpler to configure.

**2. Smart subreddit discovery.** Relevance-weighted scoring replaces pure frequency count. Each candidate subreddit is scored by `frequency x recency x topic-word match`, and a `UTILITY_SUBS` blocklist filters noise subs like r/tipofmytongue. Search "Claude Code skills" and get r/ClaudeAI, r/ClaudeCode, r/openclaw - not generic programming subs.

**3. Top comments elevated.** The best comment on each Reddit thread now carries a 10% weight in engagement scoring and displays prominently with upvote counts. Reddit's value is in the comments - now the skill surfaces them.

Plus: **Instagram Reels** (v2.8), **Polymarket prediction markets** (v2.5), **YouTube transcripts** (v2.1), **bundled X search** - no external CLI needed.

## Beta Test Results (v2.9)

| Topic | Time | Threads | Discovered Subreddits |
|-------|------|---------|----------------------|
| Claude Code skills | 77.1s | 99 | r/ClaudeAI, r/ClaudeCode, r/openclaw |
| Kanye West | 71.7s | 84 | r/hiphopheads, r/NFCWestMemeWar, r/Kanye |
| Anthropic odds | 68.0s | 65 | r/Anthropic, r/ClaudeAI, r/OpenAI |
| Best rap songs lately | 68.9s | 114 | r/BestofRedditorUpdates, r/rap, r/TeenageRapFans |
| Nano Banana Pro | 66.6s | 99 | r/GeminiAI, r/nanobanana2pro, r/macbookpro |

## What's New

### Added
- ScrapeCreators Reddit backend with keyword search and subreddit discovery
- Smart subreddit discovery with relevance-weighted scoring
- Utility subreddit blocklist (`UTILITY_SUBS`)
- Top comment scoring (10% engagement weight) and prominent rendering
- Comment excerpts increased to 400 chars, insights raised to 10

### Changed
- `primaryEnv` → `SCRAPECREATORS_API_KEY` (one key for Reddit, TikTok, Instagram)
- Reddit engagement scoring: `0.55/0.40/0.05` → `0.50/0.35/0.05/0.10`
- SKILL.md synthesis instructions emphasize quoting top comments

### Fixed
- Utility sub noise in subreddit discovery
- Reddit no longer requires `OPENAI_API_KEY`

## New Contributors

- @JosephOIbrahim -- Windows Unicode fix ([#17](https://github.com/mvanhorn/last30days-skill/pull/17))
- @levineam -- Model fallback for unverified orgs ([#16](https://github.com/mvanhorn/last30days-skill/pull/16))
- @jonthebeef -- `--days=N` configurable lookback ([#18](https://github.com/mvanhorn/last30days-skill/pull/18))

## Credits

- [@steipete](https://github.com/steipete) -- Bird CLI (vendored X search) and yt-dlp/summarize inspiration for YouTube transcripts
- [@galligan](https://github.com/galligan) -- Marketplace plugin inspiration
- [@hutchins](https://x.com/hutchins) -- Pushed for YouTube feature

## Install

```bash
# Claude Code
git clone https://github.com/mvanhorn/last30days-skill.git ~/.claude/skills/last30days

# Codex CLI
git clone https://github.com/mvanhorn/last30days-skill.git ~/.agents/skills/last30days
```

30 days of research. 30 seconds of work. Eight sources. Zero stale prompts.
