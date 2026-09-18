# Anthropic Host Adapter

Read this reference only when Claude Code, Claude.ai, or Anthropic's Skills API
is a target runtime or Deployment Target. Verify current official documentation
before changing a managed installation or uploading through an API.

## Classification and precedence

- **[Anthropic]** Rules in this file describe Anthropic surfaces. They don't
  become universal Agent Skills requirements.
- **[Protocol]** Keep one portable, protocol-compliant `SKILL.md` as the core.
- **[General guidance]** Add Anthropic-only fields or execution behavior
  conditionally; don't maintain a second Claude-specific skill body.

## Claude Code locations and discovery

- **[Anthropic]** Choose location by intended audience: personal skills live at
  `~/.claude/skills/<skill-name>/SKILL.md`, project skills at
  `.claude/skills/<skill-name>/SKILL.md`, plugin skills under
  `<plugin>/skills/<skill-name>/SKILL.md`, and enterprise skills through
  managed settings.
- **[Anthropic]** A project-local skill is a supported outcome, including when
  its workflow is specific to that repository. Keep always-loaded project
  facts or conventions in project instructions instead of forcing them into
  an on-demand skill.
- **[Anthropic]** Claude Code discovers skills from parent and nested
  directories. Account for that when choosing project placement; inspect the
  current project and its local instructions before creating a duplicate or
  shadowed skill.
- **[General guidance]** Keep the selected editable directory as the Canonical
  Source. Treat plugin installs, managed copies, and other runtime-discovered
  copies as Deployment Targets unless the user explicitly assigns ownership
  there.

## Claude Code frontmatter and invocation

- **[Anthropic]** Claude Code supports host fields beyond the portable floor,
  including `when_to_use`, `argument-hint`, `arguments`,
  `disable-model-invocation`, `user-invocable`, `context`, `agent`,
  `allowed-tools`, and `disallowed-tools`. Confirm current host documentation
  before relying on a field.
- **[Anthropic]** Write `description` as what the skill does plus when to use
  it. Put the key use case first, because Claude selects from listing
  metadata and may truncate it under context pressure.
- **[Anthropic]** Set `disable-model-invocation: true` for workflows that must
  be user-triggered, especially side-effectful actions whose timing Claude
  must not choose. This also changes whether the skill description is loaded
  for model discovery.
- **[Anthropic]** Set `user-invocable: false` only for background knowledge
  that shouldn't appear as a slash command. This does not by itself prevent
  Claude from invoking the skill.
- **[Anthropic]** Treat `allowed-tools` as pre-approval. Claude Code's
  permission model still bounds the effect. Use `disallowed-tools` for a
  temporary restriction, and use permission settings for durable policy.
- **[Anthropic]** Use `context: fork` only for a self-contained task that can
  run without conversation history. Don't fork a passive guideline skill that
  has no actionable prompt.
- **[Anthropic]** If a forked skill specifies `agent`, verify that the chosen
  agent's context and tools fit the work; some built-in agent types omit
  project context that the task may need.
- **[Anthropic]** Use supported argument and string substitutions only after
  checking current syntax. Treat command interpolation or shell-backed
  context as executable behavior and review its inputs, permissions, and
  failure modes.
- **[Anthropic]** Loaded skill content stays in the Claude Code conversation.
  It is not re-read on every turn. Re-read the Canonical Source explicitly
  before editing or resolving possible drift.

## Claude.ai, API, and managed deployment

- **[Anthropic]** Treat Claude Code, Claude.ai, and API uploads as separate
  surfaces that don't automatically synchronize.
- **[Anthropic]** Treat API and managed workspace uploads as Deployment
  Targets derived from a durable source. Don't keep separate bodies for those
  copies.
- **[Anthropic]** Anthropic recommends source control for history, review, and
  rollback when an organization distributes skills across surfaces.
- **[Anthropic]** API requests support a bounded number of simultaneous
  skills; check the current documented limit and evaluate recall before
  consolidating or routing a larger catalog.
- **[Anthropic]** Pin reviewed versions for production-style deployment. Keep
  rollback history of where each version came from. Re-run evaluation and
  security review for updates.
- **[General guidance]** Upload, organization-wide deployment, replacement,
  rollback, and deletion are separate external mutations. Require
  authorization for the requested action and report partial target results
  independently.

## Anthropic authoring guidance

- **[Anthropic]** Keep the `SKILL.md` body under 500 lines, place additional
  detail in directly linked files, avoid deeply nested references, and add a
  table of contents to long references.
- **[Anthropic]** Write specific, third-person descriptions. Include what the
  skill does, when to use it, and relevant key terms.
- **[Anthropic]** Keep examples concrete and terms consistent. Make workflows
  explicit. Keep time-sensitive claims out of the durable core, or mark them
  for re-verification.
- **[Anthropic]** When the behavior is testable enough, establish
  representative evaluation gaps and baselines before writing a lot of
  guidance. Don't turn that into a hard requirement for every subjective or
  low-risk edit.
- **[Anthropic]** Test on the models and surfaces intended for deployment.
  Don't claim cross-model or cross-surface behavior from a single passing
  run.
- **[Anthropic]** Review network calls, credentials, broad filesystem access,
  path traversal, executable code, and instruction manipulation as security
  surfaces before enterprise deployment.

## Anthropic validation

- **[Protocol]** Validate the shared body against the Agent Skills
  specification.
- **[Anthropic]** Validate Claude Code discovery, frontmatter, invocation
  controls, substitutions, permissions, and fork behavior used by this skill.
- **[Anthropic]** Validate Claude.ai or API deployment separately and record
  the deployed version or checksum when the interface exposes one.
- **[General guidance]** Report Claude Code, Claude.ai, API, and managed
  targets using the host-neutral action and verification fields in the
  Sources and Deployment reference loaded directly from `SKILL.md`; don't add
  Anthropic-only statuses. Map an unavailable surface to
  `action_status: blocked` and unverifiable read-back after a completed
  action to `verification_status: unknown`.

## Official sources

- [Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Skills for enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)
