---
name: prd
description: Use when writing a PRD from a Linear ticket or feature request. Triggers on "write PRD", "create requirements doc", "PRD from ticket".
allowed-tools:
  - Bash
  - Read
  - Grep
  - mcp__Linear__*
---

# PRD from Linear Ticket

Write a **concise, implementation-ready PRD** from a Linear ticket or project.

## Usage

```
/prd <LINEAR_TICKET_ID>
```

**Examples:**
```bash
/prd ABC-123
/prd https://linear.app/your-team/issue/ABC-123
```

## What It Does

### 1. Gather Inputs
- Fetches ticket/project from Linear (title, description, acceptance criteria)
- Retrieves linked designs, mocks, or prior context
- If image URLs exist without captions, adds descriptive captions
- Asks for missing inputs if needed

### 2. Analyze Ticket
- Reads the ticket title and description (may be high-level)
- Examines codebase for existing relevant code and features
- Understands technical context and constraints

### 3. Write PRD

Creates a Product Requirements Document with these sections:

```markdown
# [Title]

## Description
[Clear summary of what we're building and why]

## Features
- Feature 1
- Feature 2

## Acceptance Criteria
- [ ] Testable criterion 1
- [ ] Testable criterion 2

## Technical Requirements
- Backend: [specifics]
- Frontend: [specifics]
- Database: [specifics]

## UI/UX Requirements
- [Design specifications]
- [User flows]

## Dependencies
- [External dependencies]
- [Internal dependencies]

## Risks
- [Technical risks]
- [Timeline risks]

## References
[Images with captions if applicable]
```

### 4. Upload PRD
- Replaces existing description in the Linear ticket with the PRD
- Adds comment: "PRD uploaded"

## PRD Quality Standards

- **Readable**: Scannable, no fluff
- **Testable**: Acceptance criteria are verifiable
- **Complete**: Covers edge cases and error conditions
- **Actionable**: Technical requirements are specific
- **Handoff-ready**: Developer can start work immediately

## Notes

- Requires Linear MCP server to be configured
- Converts ambiguous language into testable statements
- Prefers bullets over prose
- Includes existing images with descriptive captions
