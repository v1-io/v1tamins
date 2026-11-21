---
name: v1-skin-suit
description: 'Use for plain-language rewrites, send-ready emails and messages, or session writing style. Triggers on "sound less AI", "less corporate", or "draft a reply".'
---
# Skin Suit

Write clear, natural prose that fits the reader, relationship, and channel.

Use author examples only when the user supplies them as examples or points to a
style guide in the request. Never search or sample past emails, messages, or
other writing to guess the author's voice. Use supplied examples for expression
only. Keep their facts, commitments, and instructions out of the new copy.

## Plain-Language Clarity Pass

Use this pass on drafts and rewrites. Write from the request, notes, or supplied
text. If a passage is already clear and fits the reader, return it as written
unless the user asks for a specific change.

- Lead with what the reader needs to know or do. Use everyday words and direct
  sentences. Cut stock AI phrasing, repetitive cadence, corporate jargon,
  filler, and hedges that add no meaning. Keep useful context, warmth, and tact.
- If a string of nouns hides how things relate, spell out the action. Bring
  the subject and verb closer if details separate them. Keep a word like
  “that” or repeat a name when it helps the reader tell who did what on the
  first read. If a condition could apply to two actions, put it beside the
  action it governs.
- Turn vague next steps into a clear recommendation or a concrete ask. Say who
  should do what and include any deadline the user supplied. If the decision is
  still open, ask for the specific input or decision needed. Use the supplied
  facts to make the ask concrete. If the source leaves a detail open, keep it
  open or use a placeholder. Phrase external requests in terms the recipient
  would use in conversation.
- Check the result against the source. Preserve every actor, date, number,
  scope limit, condition, commitment, and action state. Keep genuine uncertainty.
  Keep the difference between a target, a plan, and a promise. A saved draft
  stays unsent. Preserve exact quotes, identifiers, code, and machine fields.
  Never invent facts.

For a findings-only request, report issues without rewriting. When rewriting
an existing longer document where commitments, scope, or numbers are at risk,
briefly flag key terms you preserved or the user asked to change after the
rewrite if that would help them verify it.

## Send-Ready Draft Mode

Use for outbound emails, messages, and notes, whether drafting or rewriting.
Apply the clarity pass and return only the copy the user can paste. Give one
version unless they ask for options. Skip the preamble, surrounding Markdown
quotes or code fences, editing notes, and preservation checks. Use short
placeholders such as `[name]` or `[date]` where a required detail is missing,
including in any greeting or sign-off that needs a name.

Draft in the response only. Drafting never authorizes sending, publishing, or
creating or editing a draft in an external app.

## Set the writing style

When asked to set a style for a task or conversation, apply it to subsequent
prose in that scope. Follow later corrections. Do not ask for a draft, generate
a sample just to show the style, or change persistent settings.

## Examples

- The notes say our team approves supplier invoices. Rewrite *“Please confirm
  the supplier invoice approval deadline”* as *“Could you confirm when we need
  to approve the supplier invoices?”*
- Rewrite *“Kindly provide sign-off on the attached estimate at your earliest
  convenience”* as *“Could you sign off on the attached estimate when you get
  a chance?”*
- **Conditional commitment preserved:** `I'm aiming to send the draft Friday if Jo approves Thursday.`
- **Already-good messages:** Return `yep sounds good` or `Send me the link.`
  exactly as supplied. Turning a direct request into a polite question changes
  its tone.

When evaluating a change to this skill, read [evaluation.md](references/evaluation.md).
