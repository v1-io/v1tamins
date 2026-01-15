---
name: analyze-tool-errors
description: Analyze LangSmith traces to identify tool error patterns and common failure modes
allowed-tools:
  - Bash
  - Read
---

# Analyze Tool Errors

Analyze tool errors from LangSmith traces to identify patterns, common failure modes, and actionable recommendations for improving agent reliability.

## Usage

```
/analyze-tool-errors [options]
```

**Options:**
- `--days <N>` - Number of days to analyze (default: 7)
- `--tool <name>` - Filter by specific tool (e.g., execute_sql, plot_data)
- `--project <name>` - LangSmith project. Omit to analyze both dev and prod.
- `--format <type>` - Output format: markdown (default) or json
- `--limit <N>` - Maximum runs to analyze (default: 5000)
- `--context` - Include system context analysis (slower, analyzes thread memories/commands)

## Examples

```bash
# Analyze both dev and prod (default)
/analyze-tool-errors

# Analyze last 30 days (both environments)
/analyze-tool-errors --days 30

# Analyze only production
/analyze-tool-errors --project humm-prod

# Analyze only development
/analyze-tool-errors --project humm-dev

# Focus on a specific tool across both environments
/analyze-tool-errors --tool execute_sql

# Get JSON output for further processing
/analyze-tool-errors --format json

# Include system context analysis (slower)
/analyze-tool-errors --context
```

## Report Contents

### Combined Summary (when analyzing both environments)
- Comparison table showing dev vs prod error rates side-by-side
- Total tool calls and errors across both environments
- Followed by detailed individual reports for each project

### Summary (per project)
- Total tool calls and error count
- Overall error rate percentage
- Number of tools and organizations affected

### Recent Relevant PRs
- Lists merged PRs from the past N days that mention tools, errors, fixes
- Helps identify if issues may have already been addressed

### Error Trend (Daily)
- ASCII bar chart showing error count by day
- Helps identify spikes or patterns over time

### Errors by Tool
| Column | Description |
|--------|-------------|
| Tool | Tool name |
| Errors | Number of errors |
| Total Calls | Total invocations (errors + successes) |
| Error Rate | Percentage of calls that failed |
| Top Error | Most common error type |

### Errors by Organization
- Shows which organizations are experiencing the most errors
- Identifies if issues are org-specific or systemic
- Resolves org IDs to names when database is accessible

### Error Classification by Timing
- **Validation errors** (<100ms): Fast failures, typically bad inputs
- **Runtime errors** (>=100ms): Slow failures, typically external issues

### Success vs Failure Input Comparison
- Shows example inputs for successful and failed calls
- Helps identify what makes inputs succeed or fail
- Useful for improving tool docstrings

### SQL Error Analysis (for execute_sql errors)
- Extracts missing tables/objects from error messages
- Identifies invalid column names
- Suggests alternative columns that exist

### Top Error Patterns
- Groups similar errors by normalized pattern
- Includes occurrence count and affected tools
- Provides direct links to:
  - LangSmith trace for debugging
  - Humm thread URL to see user context

### Actionable Fixes
- Prioritized list of tools to fix by impact
- Includes fix type recommendation:
  - `docstring`: Improve tool documentation
  - `schema_search`: Improve schema discovery
  - `investigation`: Manual review needed

### Unknown/Hallucinated Tools
- Identifies tool names that don't match known patterns
- Categorizes as "likely hallucinated" (random names) vs "likely new integrations" (follows naming patterns)
- Helps identify when agent is inventing tool names
- Also catches new SaaS integrations not yet in the known list

### System Context Analysis (requires `--context` flag)
- Analyzes thread context that may have contributed to errors
- Tracks errors in threads with:
  - Slash commands (e.g., `/qbr-prep`, `/analyze`)
  - Memories/procedural context
- Helps identify if accepted memories contain incorrect tool instructions
- Sample contexts show the query, slash command, and memory presence
- Disabled by default for performance (adds ~40 seconds per project)

## Notes

- Requires `LANGSMITH_API_KEY` environment variable
- Default project is from `LANGSMITH_PROJECT` env var or "humm-dev"
- Pattern detection normalizes UUIDs, long numbers, and quoted strings
- Script location: `services/analyst/scripts/analyze_tool_errors.py`
- Uses `gh` CLI for PR lookup (optional, gracefully skips if unavailable)
- Connects to config database for org name lookup (optional, falls back to UUIDs)
- Thread URLs: `app.heyhumm.ai` for prod, `localhost:3000` for dev
