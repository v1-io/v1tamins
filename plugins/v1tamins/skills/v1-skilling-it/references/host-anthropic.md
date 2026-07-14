# Anthropic Host Adapter

Read this reference only when Claude Code, Claude.ai, or Anthropic's Skills API
is a target runtime or Deployment Target. Verify current official documentation
before changing a managed installation or uploading through an API.

## Classification and precedence

- **[Anthropic]** Rules in this file describe Anthropic surfaces and do not
  become universal Agent Skills requirements.
- **[Protocol]** Keep one portable, protocol-compliant `SKILL.md` as the core.
- **[General guidance]** Add Anthropic-only fields or execution behavior
  conditionally; do not maintain a second Claude-specific skill body.

## Claude Code locations and discovery

- **[Anthropic]** Choose location by intended audience: personal skills live at
  `~/.claude/skills/<skill-name>/SKILL.md`, project skills at
  `.claude/skills/<skill-name>/SKILL.md`, plugin skills under
  `<plugin>/skills/<skill-name>/SKILL.md`, and enterprise skills through managed
  settings.
- **[Anthropic]** Treat a project-local skill as a supported outcome, including
  when its workflow is specific to that repository. Keep always-loaded project
  facts or conventions in project instructions instead of forcing them into an
  on-demand skill.
- **[Anthropic]** Account for Claude Code discovery from parent and nested
  directories when choosing project placement; inspect the current project and
  its local instructions before creating a duplicate or shadowed skill.
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
- **[Anthropic]** Write `description` as capability plus activation context and
  front-load the key use case because Claude uses listing metadata for
  selection and may truncate it under context pressure.
- **[Anthropic]** Set `disable-model-invocation: true` for workflows that must be
  user-triggered, especially side-effectful actions whose timing Claude must not
  choose. This also changes whether the skill description is loaded for model
  discovery.
- **[Anthropic]** Set `user-invocable: false` only for background knowledge that
  should not appear as a slash command; this does not by itself prevent Claude
  from invoking the skill.
- **[Anthropic]** Treat `allowed-tools` as a pre-approval mechanism whose effect
  is bounded by Claude Code's permission model. Use `disallowed-tools` for a
  temporary restriction, and use permission settings for durable policy.
- **[Anthropic]** Use `context: fork` only for a self-contained task that can run
  without conversation history. Do not fork a passive guideline skill that has
  no actionable prompt.
- **[Anthropic]** If a forked skill specifies `agent`, verify that the chosen
  agent's context and tools fit the work; some built-in agent types omit project
  context that the task may need.
- **[Anthropic]** Use supported argument and string substitutions only after
  checking current syntax. Treat command interpolation or shell-backed context
  as executable behavior and review its inputs, permissions, and failure modes.
- **[Anthropic]** Remember that loaded skill content remains in the Claude Code
  conversation rather than being re-read on every turn. Re-read the Canonical
  Source explicitly before editing or resolving possible drift.

## Claude.ai, API, and managed deployment

- **[Anthropic]** Treat Claude Code, Claude.ai, and API uploads as separate
  surfaces that do not automatically synchronize.
- **[Anthropic]** Treat API and managed workspace uploads as Deployment Targets
  derived from a durable source, not as an excuse to maintain divergent bodies.
- **[Anthropic]** Anthropic recommends source control for history, review, and
  rollback when an organization distributes skills across surfaces.
- **[Anthropic]** API requests support a bounded number of simultaneous skills;
  check the current documented limit and evaluate recall before consolidating or
  routing a larger catalog.
- **[Anthropic]** Pin reviewed versions for production-style deployment, retain
  rollback provenance, and re-run evaluation and security review for updates.
- **[General guidance]** Upload, organization-wide deployment, replacement,
  rollback, and deletion are separate external mutations. Require authorization
  for the requested action and report partial target results independently.

## Anthropic authoring guidance

- **[Anthropic]** Keep the `SKILL.md` body under 500 lines, place additional
  detail in directly linked files, avoid deeply nested references, and add a
  table of contents to long references.
- **[Anthropic]** Use specific, third-person descriptions containing capability,
  activation context, and relevant key terms.
- **[Anthropic]** Keep examples concrete, terminology consistent, workflows
  explicit, and time-sensitive claims out of the durable core or clearly marked
  for re-verification.
- **[Anthropic]** Establish representative evaluation gaps and baselines before
  writing extensive guidance when the behavior is sufficiently testable. Do not
  turn that recommendation into an absolute requirement for every subjective or
  low-risk edit.
- **[Anthropic]** Test on the models and surfaces intended for deployment; do
  not claim cross-model or cross-surface behavior from a single passing run.
- **[Anthropic]** Review network calls, credentials, broad filesystem access,
  path traversal, executable code, and instruction manipulation as security
  surfaces before enterprise deployment.

## Anthropic validation

- **[Protocol]** Validate the shared body against the Agent Skills
  specification.
- **[Anthropic]** Validate Claude Code discovery, frontmatter, invocation
  controls, substitutions, permissions, and fork behavior used by this skill.
- **[Anthropic]** Validate Claude.ai or API deployment separately and record the
  deployed version or checksum when the interface exposes one.
- **[General guidance]** Report Claude Code, Claude.ai, API, and managed targets
  using the host-neutral action and verification fields in the Sources and
  Deployment reference loaded directly from `SKILL.md`; do not add
  Anthropic-only statuses. Map an unavailable surface to
  `action_status: blocked` and unverifiable read-back after a completed action to
  `verification_status: unknown`.

## Official sources

- [Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Skills for enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)
