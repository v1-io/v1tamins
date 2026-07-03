---
"v1tamins": minor
---

Refactor the interview skill, adopt changesets for releases, and add an out-of-scope knowledge base.

- **v1-interview-me** now composes a single interview loop (`references/interview-loop.md`) instead of a ~300-line monolith, attaches a recommended answer to every question, and gains an opt-in with-docs mode that writes resolved glossary terms and gated ADRs during the session. `v1-shared-language` supports inline single-term upserts to back it.
- **Releases** are now changeset-driven: `npm run version` bumps `package.json`, generates `CHANGELOG.md`, and mirrors the version into both runtime plugin manifests. Validation enforces three-way version parity, and CI requires a changeset for plugin content changes — contributors add a changeset instead of hand-bumping manifests.
- **`.out-of-scope/`** records rejected skill and design directions with durable reasons so they are not re-proposed.
