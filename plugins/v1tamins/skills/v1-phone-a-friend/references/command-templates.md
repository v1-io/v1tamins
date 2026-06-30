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

## Inlining a Named Skill's Rubric

A peer runtime usually does not have your named skills installed (the peer-capability rule in `SKILL.md`). When you want a peer to apply a specific rubric — a review standard, a quality bar — do not name the skill and hope; resolve the skill's `SKILL.md` at runtime and inline its body into the task, then have the peer report `Capability path actually used: prompt-only fallback`.

Resolve the rubric by searching the installed skills roots at runtime rather than committing a host-specific path:

```bash
# Find a named skill's SKILL.md across the installed skills roots (first match wins).
# Roots vary by host/runtime; glob the plausible ones and degrade if none match.
find_skill_rubric() {
  name="$1"
  for root in \
    "$HOME"/.claude/plugins/*/*/*/skills "$HOME"/.claude/skills \
    "$HOME"/.codex/*/skills "$HOME"/.cursor/*/*/*/skills; do
    [ -d "$root" ] || continue
    hit="$(find "$root" -maxdepth 3 -type f -path "*/$name/SKILL.md" 2>/dev/null | head -1)"
    [ -n "$hit" ] && { printf '%s\n' "$hit"; return 0; }
  done
  return 1
}

RUBRIC_FILE="$(find_skill_rubric "<skill-name>")" || RUBRIC_FILE=""
RUBRIC_BLOCK=""
[ -n "$RUBRIC_FILE" ] && RUBRIC_BLOCK="$(printf '===== RUBRIC: %s =====\n%s\n===== END RUBRIC =====\n' "<skill-name>" "$(cat "$RUBRIC_FILE")")"
```

Embed `"$RUBRIC_BLOCK"` in `PHONE_A_FRIEND_TASK` (under the review lens). If `RUBRIC_FILE` is empty the rubric is unavailable in this environment — apply the standard inline from your own knowledge and still report `prompt-only fallback`, or skip that lens and record it as degraded. The glob roots above are illustrative; adapt them to the host without committing one machine's exact cache path.

## Supervised Local Runs

Background launch is the **default** for any peer run that could exceed the host's command timeout — never foreground-`wait` on a peer, because the host's timeout (e.g. an agent's 2-minute Bash default) sends a signal to the parent's process group and reaps the backgrounded peer along with the wait. A bare `( <peer-command> ) &` does **not** survive this: the subshell stays in the parent's process group. Use the bundled `peer-run.sh` helper, which detaches each peer into its own session (`setsid`, falling back to `nohup` + `disown`) so a parent-shell timeout cannot reap it.

Resolve the helper relative to this skill's directory at runtime (the skill ships it at `scripts/peer-run.sh`); do not hardcode an absolute or checkout path. Then:

```bash
PEER_RUN="<this skill dir>/scripts/peer-run.sh"
RUN_DIR="<host-scratch-dir>/v1-phone-a-friend/<run-slug>"

# Launch each peer with a distinct slug under one run dir (multi-peer = N launches):
"$PEER_RUN" launch --dir "$RUN_DIR" --slug codex  -- <codex-wrapper>
"$PEER_RUN" launch --dir "$RUN_DIR" --slug claude -- <claude-wrapper>

# Poll across turns until each slug is complete or stalled, then read the verdict:
"$PEER_RUN" status  --dir "$RUN_DIR" --slug codex     # running | complete | stalled
"$PEER_RUN" verdict --dir "$RUN_DIR" --slug codex     # complete | stalled (judged by output, not exit code)
"$PEER_RUN" teardown --dir "$RUN_DIR" --slug codex    # PID-scoped kill; never pkill -f
```

The helper owns the contract: stdin closed per launch, detached background, a `peer.pid`/`peer.done` sentinel pair, PID-scoped teardown (never a pattern kill that could reap an unrelated peer), and a completion **verdict judged by substantive output rather than exit code** — a peer that returned real content under a nonzero/odd exit code is `complete`; an empty success exit is `stalled`. Before launching, set `<host-scratch-dir>` to a host-appropriate scratch location and record the run directory, first-progress deadline, and check-in cadence. If `status` stays `running` past the first-progress deadline with no output growth, retry once with a narrower prompt, switch peers, or mark that peer `stalled`. On hosts without `setsid` and for long runs, also use the host's own background primitive (e.g. Claude Code `run_in_background`) — the helper's detachment is best-effort-portable, not a universal guarantee.

If the helper is unavailable, the manual equivalent is `( <peer-command> </dev/null >"$RUN_DIR/<peer>.stdout" 2>"$RUN_DIR/<peer>.stderr"; printf 'DONE rc=%s\n' "$?" >"$RUN_DIR/<peer>.done" ) &` with `$!` saved to `<peer>.pid` — but this lacks true detachment, so pair it with the host's background primitive.

## Command Wrapper Matrix

| Peer | `readonly` wrapper | `local-verify` or `isolated-delegate` wrapper |
| --- | --- | --- |
| Claude Code | `claude -p --allowedTools "Read,Grep,Glob" --disallowedTools "Edit,Write,Bash" ...` | `claude -p --permission-mode bypassPermissions ...` |
| Codex | `codex exec --sandbox read-only --cd <repo> ...` | `codex exec --dangerously-bypass-approvals-and-sandbox --cd <repo> ...` |
| Cursor Agent | `cursor-agent -p --mode plan --trust ...` | `cursor-agent -p --worktree <name> --force ...` |
| Gemini CLI | Use documented read-only or plan flags when available. | Use full-access flags only in a trusted or isolated worktree. |

Resolve model, effort, permission flags, and output modes from current local help, model lists, config, or the user's explicit request. Do not pin concrete model names in reusable commands, and do not invent permission-mode values that local help does not document.

Two stall-killers apply to every wrapper above and are baked into the per-peer sections: close stdin (`< /dev/null`) so a prompt-as-argument run does not block on stdin, and prefix Claude runs with `env -u ANTHROPIC_API_KEY` so a stale env key cannot shadow the logged-in account. The capability-audit probes (`claude doctor`, etc.) can themselves hang — bound them (e.g. wrap in the host's timeout) and treat a probe that does not return as `auth: not checked`, never as a blocker.

## Claude Code

Read-only consult:

```bash
env -u ANTHROPIC_API_KEY claude -p \
  --allowedTools "Read,Grep,Glob" \
  --disallowedTools "Edit,Write,Bash" \
  --output-format stream-json \
  --model <model-or-alias> \
  "$PHONE_A_FRIEND_PROMPT" < /dev/null
```

Trusted verification or isolated delegation:

```bash
env -u ANTHROPIC_API_KEY claude -p \
  --permission-mode bypassPermissions \
  --output-format stream-json \
  --model <model-or-alias> \
  --effort <effort-level> \
  "$PHONE_A_FRIEND_PROMPT" < /dev/null
```

Prefix `env -u ANTHROPIC_API_KEY` so a stale or invalid `ANTHROPIC_API_KEY` in the environment cannot override the logged-in Claude account and silently fail auth. Keep `--output-format stream-json` so progress is observable and an empty response is distinguishable from a stall, and close stdin (`< /dev/null`) for the same reason as Codex.

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
  "$PHONE_A_FRIEND_PROMPT" < /dev/null
```

Trusted verification or isolated delegation:

```bash
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --cd <trusted-or-isolated-repo> \
  --json \
  --model <model> \
  "$PHONE_A_FRIEND_PROMPT" < /dev/null
```

Always close stdin (`< /dev/null`) when the prompt is passed as an argument. Without it, `codex exec` blocks on `Reading additional input from stdin` and the run stalls with no output — a recurring, silent failure.

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
