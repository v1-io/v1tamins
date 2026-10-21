# Repository instructions

v1tamins distributes reusable AI development skills as one plugin for Claude
Code and Codex. It ships skill text, routing metadata, and executable helpers.

## Source and distribution

- The Canonical Source is `plugins/v1tamins/skills/v1-<name>/`: one skill
  directory with `SKILL.md`, `agents/openai.yaml`, and any required resources.
  Both runtime plugin manifests consume this shared directory.
- Marketplace manifests live in `.agents/plugins/` and `.claude-plugin/`.
  Installation and the skill catalog are documented in `README.md`.
- Private `v1-_*` skill directories are ignored and are not distributed.
- Use `v1-skilling-it` for skill authoring and maintenance. Check
  `.out-of-scope/` before proposing a new skill or structural change.

## Public-safe contributions

Every committed file may be read publicly. Keep reusable workflows and decision
rules; replace private facts with placeholders such as `<repo>` or `<service>`.
Never commit secrets, account IDs, private customer names, internal URLs,
incident details, absolute home paths, or private-project instructions.

Shared guidance must use packaged skills or documented public dependencies.
The bounded checker in `scripts/check-shared-portability.py` rejects known
personal dependencies and home paths; it does not replace reviewing the diff.
Document installation and missing-dependency behavior before extending its
public companion allowance.

## Skill metadata

A trigger is user language that selects a skill. Keep the frontmatter
`description` focused on the core purpose and distinct natural triggers;
target 180 characters or fewer. Put methods and edge cases in the body or a
linked reference. The frontmatter `name` must match the `v1-*` directory.

Declare `policy.invocation_posture` in each skill's `agents/openai.yaml`:

- `implicit`: ordinary local work, selectable by the model.
- `selective_implicit`: model-selectable, with consequential actions separately
  gated; set `allow_implicit_invocation: true`.
- `explicit_only`: human or named automation invocation; set
  `allow_implicit_invocation: false` and `disable-model-invocation: true` in
  `SKILL.md`.

Declare `policy.side_effects` for external writes, Git remote changes, peer
launches, or browser capture. Keep orchestration entry points `v1-implement-unit`,
`v1-review-board`, `v1-pr`, and `v1-land-pr` explicit. Child routing does not
open a parent workflow. There is no supported `agent-only` posture.

## Contribution workflow

1. Edit the canonical skill and required bundled resources.
2. Update `v1-menu` when a skill is added, renamed, removed, or changes posture.
   Update the README count, catalog, and entry points when the catalog changes.
3. Add a changeset for distributed package changes. Changesets owns version
   bumps and changelog generation; `scripts/sync-plugin-versions.sh` keeps
   `package.json` and both runtime plugin manifests in agreement.
4. Run `scripts/validate-plugin.sh --verbose` for static packaging checks.
   Run affected offline tests for executable helper or checker changes; the
   commands are in `.github/workflows/validate.yml`.
5. Verify changed skill behavior proportionately in a real project. Static
   checks establish packaging consistency, not runtime selection or behavior.
6. Review the changed files for privacy, portability, and broken references.

Keep README and these instructions aligned. `CLAUDE.md` imports this file.
README images need meaningful alt text; generated images keep an adjacent
`.imagegen.md` prompt and provenance record. Update that record when changing
its image.

## Tracker

Use the public GitHub Issues route in `docs/agents/issue-tracker.md`.
For triage labels, read `docs/agents/triage-labels.md`.
