---
name: v1-prd
description: Use when writing a PRD from a Linear ticket or feature request. Triggers on "write PRD", "create requirements doc", "PRD from ticket".
allowed-tools:
  - Bash
  - Read
  - Grep
---
# PRD from Linear Ticket

Write a **concise, implementation-ready PRD** from a Linear ticket or project.

## Usage

Typical invocations:
- Claude Code: `/v1-prd <LINEAR_TICKET_ID>`
- Codex: invoke `v1-prd` from the skills menu or use `$v1-prd <LINEAR_TICKET_ID>`

Examples:
```bash
/v1-prd ABC-123
/v1-prd https://linear.app/your-team/issue/ABC-123
```

In Codex, the slash examples below map directly to `$v1-prd ...`.

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
- Extracts customer evidence when available: current workaround, triggering circumstance, desired progress, competing solutions, adoption obstacles, and buying/approval path
- Identifies the user-facing conceptual model: core objects, states, relationships, actions, permissions, and feedback the product must make visible
- Flags hidden state, mode switches, ambiguous object ownership, destructive actions, or memory burdens that need explicit requirements
- Adds a compact customer-job section when the request is driven by customer discovery, market validation, or a new product wedge. Use the full Job Spec template in [v1-learning-from-customers](../v1-learning-from-customers/SKILL.md) when detail is needed.

### 3. Write PRD

Creates a Product Requirements Document with these sections:

```markdown
# [Title]

## Description
[Clear summary of what we're building and why]

## Customer Job
[When customer evidence exists: summarize the customer slice, triggering circumstance, desired progress, current workaround, adoption obstacle, and success signal. Use the full Job Spec template in `v1-learning-from-customers` when the PRD needs deeper JTBD detail.]

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

## Conceptual Model
- Objects: [entities the user must understand]
- States: [visible states, pending states, success/failure states]
- Actions: [what the user can do to each object]
- Feedback: [how the user knows an action succeeded, failed, or is pending]
- Constraints: [invalid, dangerous, or impossible actions the product prevents]

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

### 4. Upload PRD (Explicit Only)
- Upload to Linear only when the user explicitly asks to update the ticket or publish the PRD
- If upload is requested, replace the existing description in the Linear ticket with the PRD
- If upload is requested, add comment: "PRD uploaded"
- If upload is not requested, return the PRD as a draft and state that Linear was not changed

## PRD Quality Standards

- **Readable**: Scannable, no fluff
- **Testable**: Acceptance criteria are verifiable
- **Complete**: Covers edge cases and error conditions
- **Actionable**: Technical requirements are specific
- **Handoff-ready**: Developer can start work immediately
- **Customer-grounded**: The PRD connects scope to a specific customer job, current workaround, switching obstacle, and success signal when customer evidence exists
- **Conceptually clear**: The PRD names the objects, states, actions, feedback, and constraints the UI must expose
- **Error-aware**: Requirements cover likely slips, mistakes, invalid inputs, destructive actions, and recovery paths

## Notes

- Requires Linear access (via whatever Linear tooling the project has wired up)
- Converts ambiguous language into testable statements
- Prefers bullets over prose
- Includes existing images with descriptive captions
- Use `v1-learning-from-customers` first when the ticket lacks concrete customer evidence or needs a customer-discovery plan before becoming a PRD
