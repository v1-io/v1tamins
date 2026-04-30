# GitHub Copilot Instructions

## Repository Context

v1tamins is a configuration distribution repository for Version1 AI development tooling. It ships shared agent skills, hooks, Cursor rules, MCP configuration, and project templates into developer-local tool directories.

This is not an application repository. There is no product runtime or build system. Quality comes from repo review, lightweight validation scripts, and testing skill behavior in real projects.

## Canonical Surfaces

- Treat `.agents/skills/<name>/SKILL.md` as the canonical shared skill source.
- Keep Codex metadata in `.agents/skills/<name>/agents/openai.yaml` short and trigger-oriented.
- Keep `claude/skills/<name>` as a compatibility entry that symlinks or mirrors the canonical `.agents/skills/<name>` skill.
- Use `scripts/sync-skill-hosts.sh --write` after creating or renaming skills, then run `scripts/sync-skill-hosts.sh` before committing.
- Do not symlink the whole `~/.agents/skills` or `~/.claude/skills` directory to this repo. The installer manages individual v1tamins-owned entries so external and personal skills stay outside the repository.

## Skill Writing Standards

- Follow `AGENTS.md` and `CLAUDE.md` for repo structure and contribution rules.
- Skill frontmatter must include `name` and `description`; descriptions should be triggering conditions, not workflow summaries.
- Keep `SKILL.md` lean. Move detailed examples, API notes, or long references into a directly linked `references/` file.
- Use imperative workflow instructions. Prefer concrete commands and validation gates over vague guidance.
- Preserve public-safe wording in shared skills. Do not add private project names, customer details, internal URLs, secrets, or incident-specific facts.
- If a skill includes scripts, reference them from `SKILL.md` and keep scripts deterministic, portable, and validated with shell syntax checks where possible.

## Validation Expectations

Run the smallest validation that matches the change:

- Skill frontmatter, host metadata, symlinks, or new/renamed skills: `scripts/sync-skill-hosts.sh`
- Shell helper changes: `bash -n <script>`
- Markdown/YAML metadata changes: parse YAML frontmatter or metadata when practical
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
