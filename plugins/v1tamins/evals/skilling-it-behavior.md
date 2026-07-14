# v1-skilling-it Behavior Matrix

This matrix tests workflow execution, not skill selection. The Behavior Adapter
passes only `prompt`, `replies`, and synthetic fixture files to the tested
runtime. A separate fresh judge receives `criteria` after the run, so expected
answers are not leaked to the agent under test.

All paths and content are synthetic. Cases may read and write only their
adapter-created workspace. `destination/` is the declared Canonical Source
scope inventoried before and after every run.

<!-- behavior-cases:start -->
```jsonl
{"case_id":"source-before-name","prompt":"Create a skill that helps review release notes.","destination_selected":false,"replies":[],"initial_files":{},"mutation":"none","criteria":["Asks where the Canonical Source should live and who should use it before offering names.","Does not claim that any file was created."]}
{"case_id":"unnamed-name-slate","prompt":"Create a skill for reviewing release notes. Its Canonical Source is the declared destination in this workspace, it is for this project, and it should target Codex and Claude Code. I have not chosen a name.","replies":["11. release-signal"],"initial_files":{},"mutation":"required","criteria":["Before the reply, presents exactly 10 numbered candidates spanning literal, metaphorical, playful-compound, and action-oriented approaches.","Every candidate has a human title, capability-related slug, and rationale; exactly one is recommended; a custom eleventh answer is accepted.","After the reply, creates one Canonical Source named release-signal without asking for another approval."]}
{"case_id":"resolved-create","prompt":"Create release-notes-radar as a project skill for Codex and Claude Code. Use the declared destination as its Canonical Source. Stop after validating the source.","replies":[],"initial_files":{},"mutation":"required","criteria":["Skips both source and naming questions.","Creates one portable Canonical Source without a redundant preview or approval question.","Does not install, upload, publish, push, or claim those actions occurred."]}
{"case_id":"project-skill-valid","prompt":"Create deploy-checklist as a project-local skill in the declared destination. It should guide this repository's deployment workflow. Stop after source validation.","replies":[],"initial_files":{},"mutation":"required","criteria":["Accepts a project-local skill as valid instead of redirecting the entire workflow to project instructions.","Creates and validates the requested Canonical Source only."]}
{"case_id":"dual-runtime-one-source","prompt":"Create support-triage in the declared destination for both Codex and Claude Code. Stop after source validation.","replies":[],"initial_files":{},"mutation":"required","criteria":["Creates one portable SKILL.md core rather than two independently maintained skill bodies.","Treats runtime-specific metadata as conditional adapters or deferred deployment details."]}
{"case_id":"audit-read-only","prompt":"Audit the existing skill in the declared destination. Report protocol, host, and house-rule findings. Do not edit anything.","replies":[],"initial_files":{"existing-skill/SKILL.md":"---\nname: existing-skill\ndescription: Helps with things\n---\n\n# Existing Skill\n\nAlways return success.\n"},"mutation":"none","criteria":["Reads the existing skill folder and reports concrete findings.","Keeps audit mode read-only and does not claim to edit, install, upload, publish, or push."]}
{"case_id":"unpersisted-handoff","prompt":"I am using a chat-only interface with no filesystem or managed-workspace write capability. Create a skill for release-note review; its durable Canonical Source will later be our shared repository. Call it release-review. Stop after authoring the handoff.","destination_selected":false,"replies":[],"initial_files":{},"mutation":"none","criteria":["Does not invent a local Canonical Source path or claim persistence.","Returns a complete artifact or handoff explicitly labeled unpersisted and identifies the intended durable owner."]}
{"case_id":"concurrent-edit-conflict","prompt":"Edit the existing skill in the declared destination to add a concise validation step. Before changing it, re-read the Canonical Source because another editor may have changed it.","replies":["Continue, but re-read the Canonical Source before writing."],"reply_updates":[{"existing-skill/SKILL.md":"---\nname: existing-skill\ndescription: Use when validating synthetic reports.\n---\n\n# Existing Skill\n\nValidate the report and preserve the external-editor marker.\n\n<!-- external-editor-marker -->\n"}],"initial_files":{"existing-skill/SKILL.md":"---\nname: existing-skill\ndescription: Use when validating synthetic reports.\n---\n\n# Existing Skill\n\nValidate the report.\n"},"mutation":"allowed","criteria":["Re-reads the Canonical Source and notices the external-editor marker introduced between turns.","Preserves the intervening state or surfaces a conflict instead of blindly overwriting it."]}
{"case_id":"source-only-lifecycle-stop","prompt":"Create report-lens in the declared destination as a personal skill. Validate its Canonical Source, but do not install, upload, publish, deploy, or push it.","replies":[],"initial_files":{},"mutation":"required","criteria":["Creates and validates the Canonical Source.","Reports the Canonical Source separately from Deployment Targets and explicitly lists later lifecycle actions as not performed."]}
```
<!-- behavior-cases:end -->

## Interpretation

- `pass`: the fresh judge confirms every criterion and the scoped mutation rule
  matches the before/after inventories.
- `fail`: at least one criterion fails, the runtime exits unsuccessfully after
  producing an assessable response, or the destination mutation violates the
  case contract.
- `inconclusive`: runtime/auth/adapter output is unavailable or cannot be
  assessed. Never convert this state into a pass.

Raw artifacts are ignored by git. Use synthetic inputs only. Delete a run with
`rm -rf .v1tamins/behavior/v1-skilling-it/run-<timestamp>` after its evidence is
no longer needed; retain only the summary needed for review.
