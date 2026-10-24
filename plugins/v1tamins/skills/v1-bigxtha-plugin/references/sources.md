# Sources and qualifications

These instructions are newly written architectural guidance. They do not fork
or require Anthropic's plugin-dev toolkit. Its component organization patterns
informed the distinction between grouped capabilities and shared resources;
canonical ownership, consumer loading, handoff contracts, and change impact
are the focus here. No substantive upstream code or text is incorporated.

## Authority and refresh

- **Protocol:** [Agent Skills specification](https://agentskills.io/specification).
  Use it for portable format and disclosure guidance. Recommendations about
  size do not establish architecture correctness thresholds.
- **Documented Claude Code behavior:**
  [skills](https://code.claude.com/docs/en/skills),
  [plugin manifest](https://code.claude.com/docs/en/plugins/manifest-reference),
  [loading](https://code.claude.com/docs/en/plugins/loading), and
  [dependencies](https://code.claude.com/docs/en/plugins/dependencies).
  Recheck path containment, installed boundary, substitutions, root instruction
  loading, and dependency support when a task relies on them.
- **Host adapters:** use the canonical authoring owner's adapters loaded
  directly from the entry point. Codex and Claude Code are this skill's initial
  execution targets. Reviewing another host's plugin does not establish tested
  execution support there.
- **Repository convention:** discover the target's own manifest, authoring,
  review, and release owners. The v1tamins layout is not a portable requirement.
- **Design guidance:** capability boundaries, shared ownership, and composition
  criteria are judgments to apply to inspected evidence, not vendor mandates.
- **Observed result:** runtime claims apply only to the host, source revision,
  and scenario actually tested. Keep them separate from source inspection.

Protocol and manifest sources were consulted on 2026-10-24. Vendor pages are
mutable. Recheck the applicable official documentation and installed tooling
before relying on a version-dependent claim. If unavailable, qualify the claim
and complete independent work; do not turn a toolkit example into a runtime
specification. This file is a source guide, not a certification of host parity.

## Upstream provenance

[plugin-dev component patterns](https://github.com/anthropics/claude-plugins-official/blob/58267944f92187b7d6a1c822165c96c81c864806/plugins/plugin-dev/skills/plugin-structure/references/component-patterns.md)
at revision `58267944f92187b7d6a1c822165c96c81c864806` are design input only.
Do not inherit its folder counts or host claims as universal rules. If future
work copies or substantively adapts material, inspect the license and notices
at that revision, retain required attribution, and record modifications before
shipping. A surrounding repository's license label does not replace that check.
