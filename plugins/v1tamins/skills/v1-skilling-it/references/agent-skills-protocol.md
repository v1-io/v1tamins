# Agent Skills Protocol

Read this reference whenever creating, editing, or validating a portable Agent
Skill. It defines the common floor. Host adapters may add behavior for their own
runtime, but they do not rewrite this protocol.

## Classification and precedence

- **[Protocol]** means the rule comes from the
  [Agent Skills specification](https://agentskills.io/specification).
- **[General guidance]** means the rule is an authoring recommendation rather
  than a format requirement.
- **[Protocol]** Apply protocol requirements before host extensions.
- **[General guidance]** When sources conflict, keep the portable protocol in
  the shared `SKILL.md` and isolate the host-specific behavior in the applicable
  host adapter.

## Required portable shape

- **[Protocol]** Create a directory containing `SKILL.md`.
- **[Protocol]** Begin `SKILL.md` with YAML frontmatter and follow it with
  Markdown instructions.
- **[Protocol]** Include `name` and `description` in frontmatter.
- **[Protocol]** Make `name` 1-64 characters using lowercase ASCII letters,
  digits, and hyphens only; do not begin or end with a hyphen, use consecutive
  hyphens, or differ from the parent directory name.
- **[Protocol]** Make `description` non-empty and no longer than 1024
  characters. Describe both what the skill does and when an agent should use it,
  including task-relevant keywords.
- **[Protocol]** Treat `license`, `compatibility`, `metadata`, and
  `allowed-tools` as optional fields. Keep `compatibility` within 500 characters
  and use it only for environment requirements. Treat `allowed-tools` as
  experimental because client support varies.
- **[Protocol]** Store additional metadata as string-to-string entries and use
  reasonably unique keys to avoid collisions.

Minimal portable example:

```markdown
---
name: release-note-review
description: Reviews release notes for omissions, ambiguity, and upgrade risk. Use when drafting or auditing product release notes.
---

# Release Note Review

Compare the draft against the shipped changes. Report each missing or ambiguous
item with its impact and a proposed correction.
```

## Optional resources

- **[Protocol]** Put executable code in `scripts/`, on-demand documentation in
  `references/`, and static output resources in `assets/` when they are needed.
- **[General guidance]** Create a resource only when a concrete use case needs
  it. Do not scaffold empty directories or placeholder files.
- **[General guidance]** Add a script when deterministic behavior or repeatedly
  rewritten code justifies it; add a reference when task-specific knowledge is
  too detailed for the core workflow; add an asset when the output consumes a
  template, image, data file, or other static resource.
- **[Protocol]** Keep scripts self-contained or document their dependencies,
  return helpful errors, and handle known edge cases.
- **[General guidance]** Keep one source of truth for each instruction. Do not
  duplicate detailed material between `SKILL.md` and a reference.

## Progressive disclosure and file references

- **[Protocol]** Assume clients load `name` and `description` for discovery,
  load the complete `SKILL.md` after activation, and load bundled resources only
  when required.
- **[Protocol]** Keep `SKILL.md` under 500 lines and move detailed material to
  focused references.
- **[Protocol]** Reference bundled files with paths relative to the skill root.
- **[Protocol]** Keep file references one level deep from `SKILL.md`; avoid a
  chain where one reference must reveal another reference.
- **[General guidance]** Link every required resource directly from `SKILL.md`
  and state the condition that makes the agent load or run it.
- **[General guidance]** Add a compact table of contents when a long reference
  would otherwise hide its scope during preview.

## Authoring contract

- **[General guidance]** Capture concrete use cases, positive and negative
  triggers, expected outputs, edge cases, dependencies, required permissions,
  and checkable success criteria before drafting instructions.
- **[General guidance]** Keep one portable `SKILL.md` for all requested runtimes.
  Add only conditional host metadata or host-specific notes; do not maintain
  parallel runtime-specific bodies.
- **[General guidance]** Match specificity to risk: use flexible prose when
  several approaches are valid, parameterized procedures when one pattern is
  preferred, and exact commands or scripts when sequence errors are costly.
- **[General guidance]** Use an exact template only when downstream structure is
  a contract. Label adaptable formats as defaults so the agent does not mistake
  a suggestion for a schema.
- **[General guidance]** Prefer concrete input/output examples when wording or
  output shape matters. Include at least one boundary or failure example when a
  happy-path example could conceal unsafe behavior.
- **[General guidance]** For branching workflows, name the decision first and
  make each branch's entry condition explicit. Move a large branch into a direct
  reference and name the condition for loading it.
- **[General guidance]** For quality-critical work, define a feedback loop with
  an artifact, validation command or observable check, correction step, and
  stop condition. Do not use an unchecked "validate and improve" instruction.
- **[General guidance]** Keep an instruction only when it changes a trigger,
  gate, artifact, command, threshold, example, failure mode, or stop rule.
- **[General guidance]** Treat a project-local skill as valid when it provides an
  on-demand workflow or reference set. Put always-loaded project facts and
  conventions in the project's instruction files instead.

## Validation

- **[Protocol]** Validate the folder against the Agent Skills format; the
  specification recommends `skills-ref validate ./path/to/skill`.
- **[General guidance]** Also validate the selected host adapter, local
  repository rules, direct links, executable resources, privacy, routing, and
  representative behavior before claiming completion.
- **[General guidance]** Report the editable Canonical Source separately from
  installs, uploads, caches, packages, or other derived Deployment Targets.
- **[General guidance]** Re-read the Canonical Source before an edit; do not edit
  a runtime cache or opaque upload as though it were authoritative.

## Conditional v1tamins house rules

Apply this section only when `plugins/v1tamins/skills/` is the selected
Canonical Source. These are repository rules, not Agent Skills requirements.

- **[v1tamins]** Prefix the skill directory and frontmatter name with `v1-`.
- **[v1tamins]** Add `agents/openai.yaml` using the repository's current
  metadata and invocation-policy schema; keep the portable workflow in the one
  shared `SKILL.md` consumed by both runtime manifests.
- **[v1tamins]** Do not add a per-skill settings file or a second
  runtime-specific skill body.
- **[v1tamins]** Update the trigger inventory and routing JSONL whenever
  description, invocation posture, OpenAI metadata, or routing-relevant body
  guidance changes.
- **[v1tamins]** Review `v1-menu` whenever a skill is added, renamed, removed,
  or changes invocation posture.
- **[v1tamins]** Add a Changeset for a distributable change; do not hand-edit
  package or plugin versions or `CHANGELOG.md`.
- **[v1tamins]** Run `scripts/validate-plugin.sh --verbose` and the repository's
  privacy and portability scan before completion.

## Source

- [Agent Skills specification](https://agentskills.io/specification)
