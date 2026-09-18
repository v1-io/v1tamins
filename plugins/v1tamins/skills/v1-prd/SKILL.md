---
name: v1-prd
description: Use when turning a Linear ticket or feature request into a PRD. Triggers on "write PRD", "requirements doc", or "PRD from ticket".
allowed-tools:
  - Bash
  - Read
  - Grep
---
# PRD from Linear Ticket

Turn a Linear ticket or project into a PRD a builder can implement from.

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

## Workflow

### 1. Gather inputs
- Fetch the ticket or project from Linear (title, description, acceptance criteria)
- Pull linked designs, mocks, or prior context
- If image URLs have no captions, add descriptive captions
- Ask for missing inputs if needed

### 2. Analyze the ticket
- Read the ticket title and description (they may be high-level)
- Look in the codebase for related code and features
- Note the technical context and constraints
- Pull customer evidence when it exists: current workaround, triggering circumstance, desired progress, competing solutions, adoption obstacles, and buying/approval path
- Name the user-facing conceptual model: core objects, states, relationships, actions, permissions, and feedback the product must make visible
- Flag hidden state, mode switches, unclear object ownership, destructive actions, or memory burdens that need explicit requirements
- Add a compact customer-job section when the request comes from customer discovery, market validation, or a new product wedge. Use the full Job Spec template in [v1-learning-from-customers](../v1-learning-from-customers/SKILL.md) when you need the detail.

### 3. Write the PRD

Use these sections:

```markdown
# [Title]

## Description
[What this is and why]

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

## Quality Bar

- Scannable. No fluff.
- Acceptance criteria can be checked.
- Covers edge cases and error conditions.
- Technical requirements are specific enough to implement.
- A developer can start without guessing.
- When customer evidence exists, connect scope to a specific customer job, current workaround, switching obstacle, and success signal.
- Name the objects, states, actions, feedback, and constraints the UI must expose.
- Cover likely slips, mistakes, invalid inputs, destructive actions, and recovery paths.

## Notes

- Requires Linear access (via whatever Linear tooling the project has wired up)
- Turn vague language into testable statements
- Prefer bullets over prose
- Include existing images with descriptive captions
- Use `v1-learning-from-customers` first when the ticket lacks concrete customer evidence or needs a customer-discovery plan before becoming a PRD
