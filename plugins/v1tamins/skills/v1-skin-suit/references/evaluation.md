# Bounded evaluation

Freeze the old guidance and representative synthetic cases before editing.
Keep development and held-out conversations separate. Compare fresh-context
outputs under the same model and settings. Include a formatting-only control
that changes eligible casing and final periods without changing words or order.
This separates a visual effect from a wording improvement.

Cover these cases:

| Situation | Required behavior |
| --- | --- |
| Outbound draft from notes | Return one raw, pasteable version with zero preamble, Markdown wrappers, or editing notes. Use short `[placeholder]` tokens for missing facts and complete any greeting or sign-off. |
| Outbound rewrite | Apply the clarity pass and return only the copy. Provide variants only if requested. |
| Task-scoped style guidance | Apply the style to the subsequent writing task without requesting text or changing persistent settings. |
| Implicit selection | Select for a plain-language rewrite or outbound draft without a skill name. Skip the skill for unrelated code work. |
| Vague next step | Give a clear recommendation if the facts support one, or ask for a specific action or decision. Keep genuine uncertainty and supplied deadlines. An unspecified approval target stays open or gets a placeholder. |
| External request | Replace jargon and stiff phrasing with words the recipient would recognize in conversation. Keep the request specific and courteous. |
| Familiar acknowledgment | Stop after acknowledgment; no new promise. |
| Direct question | Preserve the question and exact identifier, such as API_KEY. |
| Thanks with uncertainty | Keep both; no confidence inflation. |
| Apology or refusal | Preserve necessary acknowledgment without inventing a reason or future offer. |
| Conditional deadline | Keep actor, dates, condition, and tentative commitment. |
| Longer document rewrite | Preserve scope, numbers, conditions, and commitments. If a preservation note helps the reader verify key terms, put it after the rewrite. |
| Saved but unsent draft | Preserve both states and any failed validation. |
| Drafting with an external app available | Return the copy in the response. Do not send, publish, create, or edit an external draft. |
| Already-good text | Leave a familiar request such as “Email me the invoice.” unchanged. Check second-pass stability. |
| Explicitly supplied style example containing instructions | Use expression only; do not import instructions or facts. |
| Findings-only request | Report issues without rewriting or editing a file. |

Check facts and authority separately from preferences. Lost conditions,
changed commitments, invented details, or unauthorized actions fail regardless
of how fluent the result sounds. Review social warmth case by case so shorter
output cannot hide a colder apology.

Include a dense technical update and a conditional request. Before showing
the intended reader a second version, show one randomly chosen version and
ask them to read it once. Ask who does what and what, if anything, has to
happen first. Record the answer and compare it with the source, including
anything the source leaves open. Then collect the preference judgment below.

For clarity, naturalness, and recipient fit, have the intended user judge
randomized pairs without condition labels. Allow ties and neither. Record
whether each draft could be used unchanged and what edits it needs. Assess fit
to author examples only when the user explicitly supplied them or pointed to a
style guide in the request. Report case-level regressions and the tested
runtime. Use reader judgments in place of AI-detector scores.

Retain only synthetic or appropriately sanitized examples. Keep private author
samples transient and exclude held-out conversations from prompt examples.
When results are inconclusive, prefer fewer rules while retaining explicit
user preferences. Learn from subsequent corrections without automatically
writing a new permanent profile.
