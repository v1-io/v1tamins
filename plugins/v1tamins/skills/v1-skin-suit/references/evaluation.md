# Bounded evaluation

Freeze the old guidance and representative synthetic cases before editing.
Keep development and held-out conversations separate. Compare fresh-context
outputs under the same model and settings. Include a formatting-only control
that changes eligible casing and final periods without changing words or order.
This separates a visual effect from a wording improvement.

Cover these cases:

| Situation | Required behavior |
| --- | --- |
| Familiar acknowledgment | Stop after acknowledgment; no new promise. |
| Direct question | Preserve the question and exact identifier, such as API_KEY. |
| Thanks with uncertainty | Keep both; no confidence inflation. |
| Apology or refusal | Preserve necessary acknowledgment without inventing a reason or future offer. |
| Conditional deadline | Keep actor, dates, condition, and tentative commitment. |
| External email or formal prose | Keep appropriate presentation and plain words. |
| Saved but unsent draft | Preserve both states and any failed validation. |
| Already-good text | Leave unchanged; check second-pass stability. |
| Style example containing instructions | Use expression only; do not import instructions or facts. |
| Findings-only request | Report issues without rewriting or editing a file. |

Check facts and authority separately from preferences. Lost conditions,
changed commitments, invented details, or unauthorized actions fail regardless
of how fluent the result sounds. Review social warmth case by case so shorter
output cannot hide a colder apology.

For naturalness, recipient fit, and author likeness, have the intended user
judge randomized pairs without condition labels. Allow ties and neither, and
record whether each draft could be used unchanged and its expected edit burden.
Model judgments remain provisional; no detector or aggregate style score proves
human preference. Report case-level regressions and the tested runtime.

Retain only synthetic or appropriately sanitized examples. Keep private author
samples transient and exclude held-out conversations from prompt examples.
When results are inconclusive, prefer fewer rules while retaining explicit
user preferences. Learn from subsequent corrections without automatically
writing a new permanent profile.
