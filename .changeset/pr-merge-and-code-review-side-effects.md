---
"v1tamins": patch
---

Fix two skill defects surfaced by the diagnosis-lens sweep:

- **v1-pr** no longer embeds a `gh pr merge --squash` command in its PR-creation flow (it sat before the review steps — a premature merge). Merging is `v1-land-pr`'s job; `v1-pr` stops at a reviewed, open PR. The attribution tagline still carries into the squash-merge commit automatically.
- **v1-code-review** now declares its `external_write` side effect (it can post reviews via `gh pr review`) and moves to `selective_implicit` posture, matching its sibling `v1-address-review` and the repo's side-effect convention. Adds the required side-effect routing fixture and updates the trigger inventory.
