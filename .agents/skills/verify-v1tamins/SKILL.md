---
name: verify-v1tamins
description: Verify v1tamins plugin loading, skill invocation, routing, or behavior in Claude Code or Codex after a change. Use for a focused live smoke check.
---

# Verify v1tamins

Run a small, manual check of the changed skill in a real runtime. This is a
project-local workflow, not part of the distributed plugin. Use the existing
runtime and its supported commands; no custom harness or fixture suite is
required.

## Choose the check

Read the changed skill and its required references. Select the affected runtime
and one representative scenario from the user's task. Before launching, record
what observable result would pass and which action boundaries must hold.

| Change | Check |
| --- | --- |
| Plugin packaging | Runtime discovers the intended plugin and skill. |
| Skill name or invocation policy | Explicit invocation loads the named skill; explicit-only skills remain unavailable for implicit invocation. |
| Description or routing | A natural request selects the intended skill; one plausible near miss does not select it. |
| Workflow instructions | The answer or artifact satisfies the changed behavior; test a failure or stop boundary when affected. |

Run `scripts/validate-plugin.sh --verbose` first. It checks package consistency;
it does not replace the selected live check. Pure documentation changes need
only link and content review unless they change runtime instructions.

## Establish the source

Record the checkout revision, uncommitted changes, runtime version, and the
actual plugin source used for the session.

- **Claude Code:** use `--plugin-dir` with the absolute checkout plugin path.
  Confirm from runtime diagnostics that this path was loaded; do not infer it
  from the answer or the plugin name alone.
- **Codex:** inspect the runtime's plugin listing to find the installed source.
  Compare that source's skill files and plugin metadata with the checkout using
  ordinary file comparison. A matching version number alone is insufficient.
  If it is stale or cannot be located, report checkout verification as blocked;
  do not overwrite installed caches to make the check pass.

Reading a checkout `SKILL.md` explicitly can test its instructions, but it
bypasses plugin discovery and implicit routing. Label that result as a direct
instruction check, not verification of the installed plugin.

## Launch and drive

Check the installed CLI's help before choosing flags. Use a fresh session and
an existing authorized login. Do not change credentials or enable API billing.
Keep tool permissions limited to the scenario; disable external connectors and
writes for read-only checks. A read-only filesystem setting alone does not
restrict external tools. Tests that require writes belong in a disposable
project with only the requested actions enabled.

For a read-only Claude check, this is a starting command from the checkout root:

```bash
claude -p --plugin-dir "$PWD/plugins/v1tamins" \
  --setting-sources '' --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --tools 'Read,Glob,Grep,Skill' --permission-mode dontAsk \
  --no-session-persistence --output-format stream-json --verbose \
  '/v1tamins:v1-menu Which skill fits reviewing a branch for merge risk? Recommend one skill and a runner-up.'
```

Confirm the namespaced skill name in the runtime's listing; use the listed
name if it differs. For an implicit-routing check, omit the skill name and
submit the natural task alone. Do not tell the runtime which skill you expect.
For Codex, use a fresh session with the verified installed plugin, or
`codex exec --sandbox read-only --ephemeral --json` after checking the configured
connectors and approval policy for the scenario.

Run one scenario at a time with a bounded foreground execution tool. Use a
120-second limit for the menu smoke check; stop and report a timeout rather
than starting another copy. Stop only the session this check created. Do not
launch background watchdogs or leave verification processes running.

## Inspect and report

Keep prompts, runtime output, and a short result under a unique ignored
`.v1tamins/verify/` run directory. Keep raw transcripts local and inspect them
for sensitive content before sharing any excerpt.

Inspect the runtime evidence and resulting answer or artifact. A skill name in
an answer is not proof it loaded; a successful exit is not proof it behaved.
If loading or routing is not observable, report that check as inconclusive.

Report the runtime and source tested, scenario, expected versus observed
behavior, evidence location, and one result per check: **pass**, **fail**, or
**inconclusive**. Missing login, stale installation, timeout, and unavailable
loading evidence are inconclusive with the specific blocker. Do not install,
publish, or broaden permissions just to turn a blocked check into a pass.
