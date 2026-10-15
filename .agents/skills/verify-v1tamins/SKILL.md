---
name: verify-v1tamins
description: Launch the v1tamins plugin in headless Claude Code and Codex, invoke or route a v1-* skill the way a user would, and keep proof on disk. Use to prove a skill loads, routes, or answers after a change.
---

# Verify v1tamins

v1tamins is a plugin, not a server. Its user surface is a runtime session:
a user types a request or `/v1-<skill>` in Claude Code or Codex and the runtime
selects, loads, and follows one `SKILL.md` from `plugins/v1tamins/skills/`.
Static checks (`scripts/validate-plugin.sh`) prove the package parses. This
skill proves the real runtimes load and use it. Read
[features/README.md](features/README.md) before driving a feature.

All commands below run from the checkout root. `$V` is the helper:

```bash
V=.agents/skills/verify-v1tamins/scripts/verify-v1tamins.py
```

## Launch

There is no long-lived process. Each drive is one headless turn that exits:

- **Claude Code**: `claude -p --plugin-dir plugins/v1tamins ...` loads the
  checkout as plugin `v1tamins@inline`, which shadows any installed
  `v1tamins@v1tamins`. It is ready when the stream-json `system/init` event
  lists `v1tamins` with `path` equal to the checkout's `plugins/v1tamins`.
- **Codex**: `codex exec --cd <checkout> --sandbox read-only --ephemeral --json`
  has no plugin-dir flag. It drives the **installed** cache
  `$HOME/.codex/plugins/cache/v1tamins/v1tamins/<version>`, so Doctor must
  prove that cache equals the checkout first. Each Codex drive rechecks parity
  before launching and records the result in its summary. Ready when the stream emits
  `thread.started`.

Create one evidence directory for the whole run and export it so every
command shares it:

```bash
export V1_VERIFY_RUN_DIR="$(python3 "$V" new-run)"
```

The helper strips API-key variables so both runtimes use the local login, never
API billing. Both commands exit on their own; there is nothing to tear down
except what [Cleanup](#cleanup) lists.

## Doctor

One read-only check that says whether this machine is worth driving:

```bash
python3 "$V" doctor
```

It reports, and exits non-zero if any requested runtime fails: `claude` on
PATH and `claude auth status` logged in; `codex` on PATH and `codex login
status` logged in; the installed Codex cache `verification_status: match`
against the checkout (via `scripts/verify-installed-plugin.sh`); the skill
count on disk. Use `--runtime claude` or `--runtime codex` to check one side.
Run it first whenever a drive looks wrong. The static validator needs a UTF-8
locale; from an agent shell with `LANG` unset, prefix it with
`LC_ALL=en_US.UTF-8` or every frontmatter check fails. A stale Codex cache means Codex
results describe the old build: update the plugin in Codex before trusting
them.

## Drive

Prompts are the user's own words. Stable handles are skill names
(`v1-<name>`), the `/v1-<name>` slash form, and routing fixture `case_id`
values from `plugins/v1tamins/evals/skill-routing.jsonl`.

- **Explicit invocation, Claude**:

  ```bash
  python3 "$V" claude --label menu --expect-skill v1-menu \
    '/v1-menu which v1 skill fits: "review this branch for merge risk before I open the PR". Name one skill and the runner-up.'
  ```

  Add `--schema <file>` to force a JSON answer (`--json-schema`), which turns
  the answer into fields instead of prose. The helper disallows Bash, Edit,
  Write, NotebookEdit, WebFetch, and WebSearch unless `--allow-writes` is set,
  so a drive can never mutate the checkout.

- **Explicit invocation, Codex**:

  ```bash
  python3 "$V" codex --label menu \
    '/v1-menu which v1 skill fits: "review this branch for merge risk before I open the PR". Name one skill and the runner-up.'
  ```

  Add `--schema <file>` for `--output-schema`. Codex runs read-only and
  ephemeral; no session is persisted.

- **Implicit routing** (does the runtime pick the right skill from a natural
  request): delegate to the repo's live routing runner, which writes under
  the run directory:

  ```bash
  python3 "$V" route --runtime claude --case-id v1-deep-review-mergerisk-positive --max-cases 1
  ```

  Any `scripts/run-skill-routing-live-eval.py` argument passes through.

Neither runtime emits a "skill loaded" event for a `/v1-*` prompt in headless
mode: the body is expanded into the turn before the model answers. Proof of
loading is therefore the init skill list (Claude) or installed-cache parity
(Codex) plus an answer that follows the skill's own contract.

## Evidence

Everything lands in `$V1_VERIFY_RUN_DIR` (default
`.v1tamins/verify/run-<utc-stamp>/`, gitignored):

- `doctor.json`: the Doctor report.
- `<label>.claude.raw.jsonl` and `<label>.codex.raw.jsonl`: the full event
  stream, including the init plugin and skill listing. This is the proof the
  runtime loaded the checkout.
- `<label>.<runtime>.summary.json`: the command (schema redacted), exit code,
  duration, plugin entry, `skills_loaded` versus on-disk, `tool_uses` or
  `tool_calls`, `final_text`, `structured_output`, and `status`.
- `<label>.<runtime>.stderr.txt`: runtime warnings.
- `routing/run-*/results.jsonl` and `summary.txt`: live routing results, one
  JSON line per case with `selected_skill`, `evidence_kind`, and `status`.

Capture the action and the result: keep the prompt in the summary and judge
the answer against the invoked skill's own contract (for `v1-menu`: one
recommendation, one runner-up, explicit skills marked). A `pass` status requires
the expected skill inventory and a successful terminal answer (Claude), or
current installed-cache parity and a completed turn with an answer (Codex); it does not grade the prose.
Read `final_text` before claiming the skill behaved.

## Cleanup

```bash
python3 "$V" cleanup
```

Completed drives retire their `pids/` records. Cleanup signals a remaining
child only when its kernel process birth identity matches the recorded one;
legacy or unverifiable records are reported under `unverified` without
signalling. Cleanup waits for a verified child to exit after TERM, then
rechecks its identity before escalating to KILL. Survivor and unverified records
remain in `pids/`, and cleanup exits non-zero. Captured-drive timeouts stop the
child process group and bound pipe cleanup. Cleanup deletes an empty `pids/`
and a `scratch/` directory if present, and lists the evidence it kept. It never
deletes evidence. Proof survives in `$V1_VERIFY_RUN_DIR`; remove old `.v1tamins/verify/run-*`
directories by hand once a review is done, since raw streams contain model
output.

Run cleanup after every failed attempt as well, so recorded PIDs do not pile
up across runs.

## Helpers

- `scripts/verify-v1tamins.py` (executable): `new-run`, `doctor`, `claude`,
  `codex`, `route`, `cleanup`. `--help` on any subcommand.
- The offline helper regressions run with `python3 scripts/test-verify-v1tamins.py`
  and are included in the static validator. They use local processes and fixture
  event streams, without launching logged-in runtimes.
- `scripts/menu-recommendation.schema.json`: structured answer shape for
  `/v1-menu` drives (`recommended_skill`, `runner_up`, `reason`).
- The repo's own `scripts/verify-installed-plugin.sh` and
  `scripts/run-skill-routing-live-eval.py` do the parity and routing work;
  this skill only points them at one evidence directory.
