# Runtime-specific skill forks

**Decision:** No forking a skill into separate Claude Code and Codex bodies
(e.g. a `-claude` / `-codex` pair, or parallel `SKILL.md` variants per runtime).

**Why:** Architecture and maintenance. One shared `plugins/v1tamins/skills/`
directory is the single source of truth for both runtimes — that is the whole
point of the sibling per-runtime manifests reading from one skills tree. Forking
a skill per runtime doubles the maintenance surface and guarantees the two
copies drift. Genuine cross-runtime differences belong in the per-runtime
metadata (`agents/openai.yaml`, invocation posture) and in small conditional
notes inside the one skill body, not in separate skill bodies.

## Prior requests
- 2026-07-02 — repo architecture review — raised while reconciling Claude Code
  vs Codex behavior; rejected in favor of one shared body plus per-runtime
  metadata.
