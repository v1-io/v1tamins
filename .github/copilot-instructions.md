# GitHub Copilot Instructions

## Repository Context

v1tamins is a public-facing configuration distribution repository for reusable AI development tooling. It ships shared agent skills, hooks, Cursor rules, MCP configuration, and project templates into developer-local tool directories.

This is not an application repository. There is no product runtime or build system. Quality comes from repo review, lightweight validation scripts, and testing skill behavior in real projects.

## Public-Safe Requirement

Assume every committed file in this repository may be read outside the original private project context. Keep guidance generalizable and remove private or project-specific details before committing.

Do not add:

- Secrets, tokens, credentials, account IDs, or environment-specific values.
- Private customer, project, person, Slack channel, dashboard, trace, or ticket details.
- Internal URLs, private domains, production incident IDs, or proprietary timelines.
- Absolute local filesystem paths such as `/Users/...`, `/home/...`, or drive-letter paths.
- Instructions that only make sense inside one private repository or one company workflow.

When extracting a lesson from a private project, keep the reusable workflow, failure mode, validation pattern, or decision rule. Replace private facts with placeholders such as `<repo>`, `<service>`, `<org-id>`, `<ticket>`, or `<incident-id>`. If the guidance cannot be made general without losing its value, leave it in that project instead of adding it to v1tamins.

## Canonical Surfaces

- Treat `.agents/skills/<name>/SKILL.md` as the canonical shared skill source.
- Keep Codex metadata in `.agents/skills/<name>/agents/openai.yaml` short and trigger-oriented.
- Keep `claude/skills/<name>` as a compatibility entry that symlinks or mirrors the canonical `.agents/skills/<name>` skill.
- Treat `plugins/v1tamins/skills/v1-<name>/` as generated mirrors that serve both the Claude Code plugin (`plugins/v1tamins/.claude-plugin/plugin.json`) and the Codex plugin (`plugins/v1tamins/.codex-plugin/plugin.json`). Do not edit those mirrors directly; edit `.agents/skills/<name>/` and re-run `scripts/sync-skill-hosts.sh --write`.
- The Claude Code marketplace manifest lives at `.claude-plugin/marketplace.json`; the Codex marketplace manifest lives at `.agents/plugins/marketplace.json`.
- Use `scripts/sync-skill-hosts.sh --write` after creating or renaming skills, then run `scripts/sync-skill-hosts.sh` before committing.
- Do not symlink the whole `~/.agents/skills` or `~/.claude/skills` directory to this repo. The installer manages individual v1tamins-owned entries so external and personal skills stay outside the repository.

## Skill Writing Standards

- Follow `AGENTS.md` and `CLAUDE.md` for repo structure and contribution rules.
- Skill frontmatter must include `name` and `description`; descriptions should be triggering conditions, not workflow summaries.
- Keep `SKILL.md` lean. Move detailed examples, API notes, or long references into a directly linked `references/` file.
- Use imperative workflow instructions. Prefer concrete commands and validation gates over vague guidance.
- Preserve public-safe wording in shared skills. Before publishing, scan for private names, URLs, absolute paths, secrets, and incident-specific facts.
- If a skill includes scripts, reference them from `SKILL.md` and keep scripts deterministic, portable, and validated with shell syntax checks where possible.

## Validation Expectations

Run the smallest validation that matches the change:

- Skill frontmatter, host metadata, symlinks, or new/renamed skills: `scripts/sync-skill-hosts.sh`
- Shell helper changes: `bash -n <script>`
- Markdown/YAML metadata changes: parse YAML frontmatter or metadata when practical
- Shared skill or instruction changes: scan the changed files for private URLs, absolute paths, secrets, tokens, customer names, and project-specific facts
- Before committing: `git diff --check`

For PR descriptions, report exactly which validations ran and do not claim unavailable checks passed.

## Review Focus

When reviewing this repository, prioritize:

- Skill instructions that are ambiguous, stale, too broad, or likely to make agents mutate the wrong thing.
- Host-surface drift between `.agents/skills`, `claude/skills`, and `agents/openai.yaml`.
- Scripts that assume a fixed branch such as `main` when they should derive base/head from GitHub or git state.
- Missing validation gates for workflows that post to GitHub, modify files, commit, push, or run external tools.
- Public-safety issues in shared skills.

Avoid requesting application-style tests, runtime architecture changes, or dependency setup unless the diff actually adds those surfaces.
