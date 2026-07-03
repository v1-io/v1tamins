# Per-skill config files

**Decision:** No per-skill configuration files (JSON/YAML settings, feature
flags, or tunables owned by an individual skill) beyond the single required
`agents/openai.yaml` metadata file.

**Why:** Scope and philosophy boundary. A v1tamins skill is meant to be
self-contained: its behavior lives in `SKILL.md` prose, and its only structured
metadata is the one `agents/openai.yaml` file the validator already checks.
Adding a config surface per skill creates state that drifts from the prose,
multiplies what a contributor and both runtimes must read to understand a skill,
and pushes behavior out of the reviewable Markdown into settings that are easy to
miss. When a skill needs to vary behavior, express it in the skill body or in the
existing metadata — not in a new config file.

## Prior requests
- 2026-07-02 — repo architecture review — raised while considering how skills
  should carry options; rejected in favor of prose + the single metadata file.
