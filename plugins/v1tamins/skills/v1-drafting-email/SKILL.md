---
name: v1-drafting-email
description: Use when the user explicitly asks to create saved Gmail drafts for review or return review links to unsent drafts.
disable-model-invocation: true
---
# Drafting Email

Create saved, unsent Gmail drafts through the available Gmail connector, verify the persisted drafts, and return direct review links.

## Safety Boundary

- Treat draft creation as an external write. Require an explicit request to create or save Gmail drafts; a request to write or suggest email copy in chat does not authorize connector use.
- Create drafts only. Do not call a send action under this skill, even when the original request also mentions sending.
- Report every draft as unsent. Leave sending for a separate, explicit action after review.

## Draft the Messages

1. Use recipients or threads named by the user. If the user asks for inbox selection, search a bounded recent window and state the selection rule.
2. Read each selected thread in full. Do not draft from snippets when surrounding context can change the reply.
3. Preserve recipients, CCs, subject, facts, dates, links, and quoted commitments from the thread. Do not invent completed actions, prices, availability, or missing facts.
4. For a reply, use the connector's exact source message identifier and preserve the thread subject. Resolve aliases to the actual correspondent only when the thread provides that address.

## Save and Verify

For each message:

1. Call the connector's create-draft action and capture its structured result, including the returned message identifier.
2. Read the created message back through the connector using that identifier.
3. Verify the read result has the `DRAFT` label and that recipients, CCs, subject, and body match the intended draft. Stop and report any mismatch instead of silently correcting or sending it.
4. Copy the read result's `display_url` into the review output. Never construct a Gmail URL from a draft identifier, message identifier, or thread identifier.
5. If `display_url` is missing, confirm the draft through the connector's list-drafts action and retry the read once. If the URL remains missing, report the missing review link instead of guessing one.

## Review Output

Lead with: `Saved as unsent Gmail drafts:`

Return exactly one bullet per verified draft:

```markdown
- [<recipient> — <subject>](<display_url>) — <summary of the outgoing draft>
```

Validate each bullet before responding:

- The link exactly equals the `display_url` returned by the connector read result.
- The label, recipient, subject, and body verification passed.
- The summary describes what the outgoing draft says, not what the incoming message asked.
- Every factual claim in the summary is supported by the verified draft body.
- The summary is one sentence of no more than 25 whitespace-delimited words.

End with: `Nothing was sent.` Do not add inbox-triage commentary unless requested.

## Synthetic Link-Provenance Check

Given this connector read result:

```json
{
  "message_id": "draft-message-123",
  "labels": ["DRAFT"],
  "to": ["jordan@example.com"],
  "subject": "Re: Recording time",
  "body": "Tomorrow works. Please use the meeting link in the calendar invitation. No special preparation is needed.",
  "display_url": "https://mail.google.com/mail/u/0/#drafts/example-message"
}
```

Accept only a review bullet whose link target is exactly `https://mail.google.com/mail/u/0/#drafts/example-message`. Reject a plausible URL assembled from `draft-message-123`; provenance from connector output is the requirement.

Valid summary:

> Confirms tomorrow works, points Jordan to the calendar's meeting link, and says no special preparation is needed.

The summary describes the outgoing draft, contains 17 whitespace-delimited words, and makes no claim absent from the verified body.
