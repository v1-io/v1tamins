---
name: v1-prd
description: Use when turning a ticket, issue, or feature request into a PRD. Triggers on "write PRD", "requirements doc", or "PRD from ticket".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Skill
---
# PRD from Ticket or Feature Request

Turn a ticket, issue, pasted request, or feature idea into a PRD a builder can
implement from.

## Usage

Typical invocations:
- Claude Code: `/v1-prd <TICKET_OR_REQUEST>`
- Codex: invoke `v1-prd` from the skills menu or use `$v1-prd <TICKET_OR_REQUEST>`

Examples:
```bash
/v1-prd https://github.com/your-org/your-repo/issues/123
/v1-prd "Add an export button for filtered results"
```

In Codex, the slash examples below map directly to `$v1-prd ...`.

## Workflow

### 1. Gather inputs
- Read the supplied ticket, issue, feature request, or pasted context (title, description, acceptance criteria)
- If an identifier or URL is supplied, use the project's documented tracker route. Do not assume a specific tracker. If the project documents no route, read it with an available tool (for example, `gh issue view <url>` for a GitHub issue) or ask the user to paste it.
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
- Label assumptions and unresolved decisions when the input is a pasted request or lacks supporting context.

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

### 4. Update the Configured Tracker (Explicit Only)
- Return the PRD as a draft and make no external changes by default.
- Update a ticket or issue only when the user explicitly asks and repository or project instructions identify a configured writable tracker.
- Post the PRD as a new comment by default. Replace the ticket or issue description only when the user explicitly asks for that.
- Use that tracker's documented route and verify the readback after updating it.
- If no configured tracker or access is available, return the draft and state that external state was unchanged or unverified.

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

- Requires access to the configured ticket or issue source only when the user asks to fetch or update it; pasted requests need no tracker access.
- Turn vague language into testable statements
- Prefer bullets over prose
- Include existing images with descriptive captions
- Use `v1-learning-from-customers` first only when the user requests customer discovery or validation, or when unresolved customer scope prevents an implementable PRD. Missing customer evidence alone does not block a pasted-request draft; label its assumptions and unresolved decisions instead.
