---
name: ralph-prd
description: Create and update prd.json for Ralph loop from a Linear ticket
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - mcp__Linear__*
---

# Ralph PRD Generator

Convert a Linear ticket into a well-structured `prd.json` for the Ralph autonomous coding loop.

## Usage

```
/ralph-prd <LINEAR_TICKET_ID>
/ralph-prd --validate
/ralph-prd --status
```

**Examples:**
```bash
/ralph-prd HUM-123
/ralph-prd https://linear.app/humm/issue/HUM-123
/ralph-prd --validate  # Check existing prd.json quality
/ralph-prd --status    # Show current story progress
```

## What It Does

### 1. Fetch Linear Ticket
- Retrieves ticket title, description, and acceptance criteria
- Fetches linked sub-issues if this is a parent ticket
- Gets any attached documents or context

### 2. Analyze Scope
- Examines the codebase to understand technical context
- Identifies affected files and components
- Notes existing patterns to follow

### 3. Break Down Into Stories
- Decomposes the ticket into small, focused user stories
- Each story must be completable in ONE Ralph iteration (~1 context window)
- Stories are ordered by dependency and priority

### 4. Generate prd.json
- Creates/updates `scripts/ralph/prd.json` with proper structure
- Ensures acceptance criteria are explicit and testable
- Adds feedback loops (typecheck, tests, browser verification)

### 5. Initialize Progress File
- Creates `scripts/ralph/progress.txt` if it doesn't exist
- Seeds with discovered codebase patterns

## Output: prd.json Structure

```json
{
  "project": "Humm",
  "branchName": "ralph/HUM-123-feature-name",
  "description": "Brief description of the feature",
  "linearTicketId": "HUM-123",
  "userStories": [
    {
      "id": "US-001",
      "title": "Short descriptive title",
      "description": "As a [user], I want [feature] so that [benefit]",
      "acceptanceCriteria": [
        "Specific, testable criterion 1",
        "Specific, testable criterion 2",
        "Typecheck passes",
        "Tests pass"
      ],
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ]
}
```

## Story Sizing Guidelines

**Right-sized stories (completable in one iteration):**
- Add a database column and migration
- Create a single UI component
- Add an API endpoint with tests
- Implement one form validation rule
- Add a filter/sort to existing list

**Stories that are TOO BIG (split these):**
- "Build entire dashboard" → Split into individual widgets
- "Implement authentication" → Split: login, signup, session, logout
- "Add user settings page" → Split into each setting section
- "Create CRUD operations" → Split: Create, Read, Update, Delete

## Acceptance Criteria Quality Standards

Each criterion MUST be:

1. **Explicit** - No ambiguous language
   - Bad: "Works correctly"
   - Good: "Returns 200 status with user object containing id, email, name"

2. **Testable** - Can be verified programmatically or visually
   - Bad: "User experience is good"
   - Good: "Loading spinner shows while fetching, disappears on complete"

3. **Include Feedback Loops** - Every story should have:
   - `"Typecheck passes"` (for TypeScript changes)
   - `"Tests pass"` (if tests exist for that area)
   - `"Verify in browser using dev-browser skill"` (for UI changes)

4. **Atomic** - One thing per criterion
   - Bad: "Form validates and saves data"
   - Good: "Form shows error for invalid email" + "Form saves on valid submit"

## Branch Naming Convention

```
ralph/HUM-XXX-kebab-case-description
```

Examples:
- `ralph/HUM-123-add-priority-filter`
- `ralph/HUM-456-user-settings-page`
- `ralph/HUM-789-fix-auth-session`

## Validation Checks

When using `--validate`, checks for:
1. All stories have unique IDs
2. All stories have at least 2 acceptance criteria
3. All stories include a typecheck/test feedback loop
4. No story is too vague (flags ambiguous language)
5. Branch name follows convention
6. Stories are properly prioritized (no gaps)

## After Generation

Once prd.json is created, start the Ralph loop:

```bash
./scripts/ralph/ralph.sh
```

Or check status:
```bash
./scripts/ralph/ralph.sh --status
```

## Files Created/Updated

| File | Purpose |
|------|---------|
| `scripts/ralph/prd.json` | User stories for Ralph to implement |
| `scripts/ralph/progress.txt` | Learnings and progress log |
| `scripts/ralph/prompt.md` | Instructions (already exists) |
| `scripts/ralph/ralph.sh` | Main loop script (already exists) |

## Updating Existing PRD

If `prd.json` already exists:
- Asks if you want to replace or merge
- Merge adds new stories while preserving completed ones
- Preserves `passes: true` for already-completed stories

## Notes

- Requires Linear MCP server to be configured
- Stories are numbered US-001, US-002, etc.
- Priority 1 = highest (implement first)
- The `notes` field is for Ralph to add implementation notes
