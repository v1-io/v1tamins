# Plugin load

Plugin load is the moment a runtime discovers the v1tamins package and lists every distributed skill, so `/v1-<name>` and autonomous routing can work at all.

## Sub-features

- `load-claude-inline` loads the checkout through `--plugin-dir` as `v1tamins@inline`, shadowing any installed copy.
- `load-claude-all-skills` lists every `plugins/v1tamins/skills/v1-*` directory as `v1tamins:v1-<name>`.
- `load-codex-parity` makes the installed Codex cache byte-equal to the checkout so Codex drives the same build.

## How to get to it (user POV)

- Start Claude Code in a project with the plugin installed or run `claude --plugin-dir <checkout>/plugins/v1tamins`; type `/v1` and see the skill list.
- Start Codex with the `v1tamins` marketplace plugin installed; type `/v1-menu` or `$v1-menu`.

## Driving it with verify-v1tamins

Preconditions:

- `python3 "$V" doctor` reports `drivable: true`.
- `V1_VERIFY_RUN_DIR` is exported.

- **Load from checkout (Claude).** Run `python3 "$V" claude --label load --max-turns 1 'Reply with exactly: ok'`. The summary shows `plugin.source` of `v1tamins@inline`, `plugin_is_checkout: true`, `skills_missing: []`, `skills_unexpected: []`, `result_subtype: success`, `result_is_error: false`, a final answer, and `skills_loaded` equal to the on-disk count reported by Doctor.
- **Installed parity (Codex).** Run `python3 "$V" doctor --runtime codex`. `codex.installed_verification.verification_status` is `match` and `installed_root` names the version from `plugins/v1tamins/.codex-plugin/plugin.json`.
- **Codex answers at all.** Run `python3 "$V" codex --label load 'Reply with exactly: ok'`. The helper first rechecks installed-cache parity. The summary shows `installed_verification.verification_status: match`, `turn_completed: true`, and `final_text` of `ok`.
- **Proof.** Keep `load.claude.raw.jsonl` (the init event is the listing) and `doctor.json`.

## Gotchas

- Claude lists skills in the `system/init` event only with `--output-format stream-json --verbose`; the helper sets both.
- A plugin named `v1tamins` installed at user scope is replaced by the inline one, not duplicated. If `plugin_is_checkout` is false the plugin-dir flag did not take effect.
- `skills_unexpected` non-empty means the runtime sees skills that are not on disk, usually a stale installed copy winning. Treat as a fail.
- Codex has no plugin-dir flag. After editing a skill, Codex keeps answering from the cache until the plugin is updated there; Doctor turns `match` into a failure so stale results are not reported as verified.
