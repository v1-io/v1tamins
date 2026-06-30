# Command Templates

Use these templates after selecting the peer, work type, and permission mode in `SKILL.md`.

## Contents

- [Prompt Contracts](#prompt-contracts)
- [Prompt Bodies](#prompt-bodies)
- [Supervised Local Runs](#supervised-local-runs)
- [Command Wrapper Matrix](#command-wrapper-matrix)
- [Claude Code](#claude-code)
- [Codex](#codex)
- [Cursor Agent](#cursor-agent)
- [Gemini CLI](#gemini-cli)

## Prompt Contracts

Ask every coding peer to return this shape:

```text
Return:
- Status: complete | partial | stalled | failed
- Recommendation
- Capability path actually used: verified named skill/plugin | verified CLI only | prompt-only fallback | unavailable
- Model requested and actual model used, if available
- Execution surface or resume handle, if available
- Output/log path, if launched as a local process
- Evidence or assumptions
- Commands run and results
- Files changed
- Final dirty state
- Risks, missing checks, and local verification steps
```

For read-only consults, require `Commands run and results: none` and `Files changed: none`.

For `local-verify` or `isolated-delegate` runs, record the starting state first:

```bash
git status --short --branch
git diff --stat
```

## Prompt Bodies

Create exactly one mode instruction, one shared task body, and one combined prompt. Pass `"$PHONE_A_FRIEND_PROMPT"` to the selected command wrapper.

Read-only consult, steelman, or review mode:

```bash
PHONE_A_FRIEND_MODE_INSTRUCTIONS="$(cat <<'MODE'
Act as an independent counterpart reviewer. Read only.
Do not edit files, create files, run commands, request broader permissions, commit, push, publish, send messages, or mutate external services.
Use `Commands run and results: none` and `Files changed: none`.
If asked to use a named skill, plugin, slash command, or subagent workflow, use it only when it is verified in this runtime and compatible with read-only headless execution. Otherwise apply the requested review standard inline and report `Capability path actually used: prompt-only fallback`.
MODE
)"
```

Trusted verification or isolated delegation mode:

```bash
PHONE_A_FRIEND_MODE_INSTRUCTIONS="$(cat <<'MODE'
Act as an independent counterpart reviewer in a trusted or isolated worktree.
You may inspect the repo and run validation commands.
Do not commit, push, publish, send messages, or mutate external services.
Before and after your work, run `git status --short --branch`.
If the run has a session id, terminal name, tmux/cmux window, cloud-agent URL, browser slug, or other resume handle, report it.
If asked to use a named skill, plugin, slash command, or subagent workflow, use it only when it is verified in this runtime. Otherwise apply the requested standard inline and report `Capability path actually used: prompt-only fallback`.
MODE
)"
```

Shared task body:

```bash
PHONE_A_FRIEND_TASK="$(cat <<'TASK'
Problem:
<one-paragraph problem statement>

Context files:
- <path>
- <path>

Question:
<specific critique, steelman, risk review, synthesis, verification, or delegated implementation request>

Return:
- Status: complete | partial | stalled | failed
- Recommendation
- Capability path actually used: verified named skill/plugin | verified CLI only | prompt-only fallback | unavailable
- Model requested and actual model used, if available
- Execution surface or resume handle, if available
- Output/log path, if launched as a local process
- Evidence or assumptions
- Commands run and results
- Files changed
- Final dirty state
- Risks, missing checks, and local verification steps
TASK
)"

PHONE_A_FRIEND_PROMPT="$(printf '%s\n\n%s\n' "$PHONE_A_FRIEND_MODE_INSTRUCTIONS" "$PHONE_A_FRIEND_TASK")"
```

If automation will consume the answer, replace the `Return` list in `PHONE_A_FRIEND_TASK` with a strict JSON schema and keep the same required fields.

## Supervised Local Runs

When launching one or more peers as local processes, create a run directory and make completion observable before waiting.

```bash
PHONE_A_FRIEND_SLUG="<short-slug>"
PHONE_A_FRIEND_SCRATCH_ROOT="<host-scratch-dir>"
PHONE_A_FRIEND_RUN_DIR="$PHONE_A_FRIEND_SCRATCH_ROOT/v1-phone-a-friend/$PHONE_A_FRIEND_SLUG"
mkdir -p "$PHONE_A_FRIEND_RUN_DIR"

# Replace `<peer-command>` with one selected wrapper below.
(
  <peer-command> \
    >"$PHONE_A_FRIEND_RUN_DIR/<peer>.stdout" \
    2>"$PHONE_A_FRIEND_RUN_DIR/<peer>.stderr"
  rc=$?
  printf 'DONE rc=%s\n' "$rc" >"$PHONE_A_FRIEND_RUN_DIR/<peer>.done"
  exit "$rc"
) &
printf '%s\n' "$!" >"$PHONE_A_FRIEND_RUN_DIR/<peer>.pid"
```

Before launching, set `<host-scratch-dir>` to an appropriate local scratch location for the host and record the run directory, first-progress deadline, maximum wait or check-in cadence, and any execution surface or resume handle. If `<peer>.stdout`, `<peer>.stderr`, `<peer>.done`, or the visible peer surface does not change by the first-progress deadline, inspect the process and artifacts, then reattach, retry once with a narrower prompt, switch peers, or mark that peer `stalled`. After completion, the parent records the exit code from `<peer>.done`; do not ask the peer to guess its wrapper exit code.

## Command Wrapper Matrix

| Peer | `readonly` wrapper | `local-verify` or `isolated-delegate` wrapper |
| --- | --- | --- |
| Claude Code | `claude -p --allowedTools "Read,Grep,Glob" --disallowedTools "Edit,Write,Bash" ...` | `claude -p --permission-mode bypassPermissions ...` |
| Codex | `codex exec --sandbox read-only --cd <repo> ...` | `codex exec --dangerously-bypass-approvals-and-sandbox --cd <repo> ...` |
| Cursor Agent | `cursor-agent -p --mode plan --trust ...` | `cursor-agent -p --worktree <name> --force ...` |
| Gemini CLI | Use documented read-only or plan flags when available. | Use full-access flags only in a trusted or isolated worktree. |

Resolve model, effort, permission flags, and output modes from current local help, model lists, config, or the user's explicit request. Do not pin concrete model names in reusable commands, and do not invent permission-mode values that local help does not document.

## Claude Code

Read-only consult:

```bash
claude -p \
  --allowedTools "Read,Grep,Glob" \
  --disallowedTools "Edit,Write,Bash" \
  --output-format stream-json \
  --model <model-or-alias> \
  "$PHONE_A_FRIEND_PROMPT"
```

Trusted verification or isolated delegation:

```bash
claude -p \
  --permission-mode bypassPermissions \
  --output-format stream-json \
  --model <model-or-alias> \
  --effort <effort-level> \
  "$PHONE_A_FRIEND_PROMPT"
```

Use full permission mode only for a trusted local repo or isolated worktree. Inspect any resulting diff before keeping it.

Do not rely on `--permission-mode plan` alone as this template's read-only Claude Code wrapper unless local help and behavior confirm the desired constraints. Prefer the explicit allow/deny tool wrapper above for read-only consults; if it is unavailable, use a disposable worktree or choose another peer.

## Codex

Read-only consult:

```bash
codex exec \
  --sandbox read-only \
  --cd <repo> \
  --json \
  --model <model> \
  "$PHONE_A_FRIEND_PROMPT"
```

Trusted verification or isolated delegation:

```bash
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --cd <trusted-or-isolated-repo> \
  --json \
  --model <model> \
  "$PHONE_A_FRIEND_PROMPT"
```

Use full permission mode only where the user trusts the repo or the worktree is disposable. Require the peer to report commands run, files changed, and final dirty state.

## Cursor Agent

Check `cursor-agent --help` locally before relying on exact flags or treating plan/ask mode as enforced read-only.

Read-only consult:

```bash
cursor-agent -p \
  --mode plan \
  --trust \
  --output-format stream-json \
  --model <model-or-auto> \
  "$PHONE_A_FRIEND_PROMPT"
```

Use `--mode ask` for pure Q&A. Use `--trust` only for a workspace the user already trusts or for a generated isolated worktree; it answers Cursor's headless workspace-trust prompt and does not replace `--mode plan` or `--mode ask`.

Do not ask headless Cursor plan/ask mode to invoke a named Cursor skill, composer workflow, or subagent workflow unless local evidence shows that workflow works in the selected mode. If a named workflow stalls or returns no output, retry with the rubric inlined as a plain prompt and report `Capability path actually used: prompt-only fallback`.

Trusted verification or isolated delegation:

```bash
cursor-agent -p \
  --worktree <name> \
  --output-format stream-json \
  --model <model-or-auto> \
  --force \
  "$PHONE_A_FRIEND_PROMPT"
```

Use `--force` only for trusted verification or delegation. If the installed CLI lacks `--mode` or `--worktree`, prefer Claude/Codex for enforced read-only consults, or run Cursor in a disposable git worktree and discard unexpected diffs after reading its answer.

## Gemini CLI

Use Gemini when installed and authenticated, especially for large-context, multimodal, or Google-grounded packets. Check `gemini --help` locally before relying on exact flags or approval modes.

Read-only consult:

```bash
gemini \
  --model <model> \
  --output-format stream-json \
  -p "$PHONE_A_FRIEND_PROMPT"
```

If local help exposes a read-only or plan approval mode, include it in the consult command. If local help exposes an auto-approve, yolo, or full-access flag, reserve that flag for trusted verification or delegation in an isolated worktree. State which flags were used when adapting to an installed CLI.
