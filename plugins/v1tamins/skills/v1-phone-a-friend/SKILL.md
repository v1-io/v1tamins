---
name: v1-phone-a-friend
description: Use when an agent needs counterpart review, another agent/model consult, steelmanning, delegated implementation, or external strong-model research. Triggers on "phone a friend", "second opinion", "ask another agent", "ask Claude", "ask Codex", "ask Cursor", "ask Oracle", "consult ChatGPT Pro", "steelman this".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - AskUserQuestion
---
# Phone a Friend

Coordinate another agent or model for counterpart review, steelmanning, delegation, deep research, or verification, then validate the result locally.

## Usage

Typical invocations:
- Claude Code: `/v1-phone-a-friend`
- Codex: invoke `v1-phone-a-friend` from the skills menu or use `$v1-phone-a-friend`

Examples:
```bash
/v1-phone-a-friend ask Claude to review this PR
/v1-phone-a-friend steelman this migration plan
/v1-phone-a-friend use Oracle Pro browser mode for this research packet
```

## Quick Start

1. Inspect the local capability surface before choosing a peer.
2. Follow the decision path below to select the peer, work type, permission mode, and reference file.
3. Package the smallest useful context and remove secrets, private URLs, customer data, tokens, account IDs, and proprietary incident details.
4. Run the selected peer with the narrowest permission mode that fits the work.
5. Treat the result as advice until verified with local evidence, tests, diffs, or source review.

## Decision Path

1. Use a direct in-agent skill instead when independence is not needed: `v1-code-review` for ordinary PR review, `v1-deep-review` for harsh maintainability review, and `v1-deep-research` for in-agent sourced research.
2. Prefer a counterpart runtime by default: Codex -> Claude Code, Claude Code -> Codex, Cursor -> Claude Code or Codex, unknown host -> best authenticated coding peer not already in use.
3. Override the counterpart default only for a named user preference or a real specialist fit: ChatGPT Pro Deep Research, Gemini long-context or multimodal review, Cursor Agent/Cloud Agent, or Oracle/browser-mode review.
4. Use the decision matrix to pick one work type and one permission mode.
5. Resolve the current model and effort from local CLI help, model lists, config, or the user's explicit request. Do not hardcode concrete model names.
6. Load the relevant reference file and run one bounded template.

## When To Use

- Use after producing a plan, diagnosis, implementation, PR description, or review that needs independent scrutiny.
- Use to steelman the best opposing argument before committing to an approach.
- Use to delegate a bounded implementation or research task to another subscribed agent when the result can be checked locally.
- Use when a specialist model/tool is materially better suited: ChatGPT Pro for true deep research, Gemini for large-context or multimodal packet review, Cursor for Cursor Agent or IDE-context workflows, Oracle/browser mode for strong external review.
- Use before a risky change when an outside critique could expose missing tests, contract breaks, simpler options, or hidden assumptions.

## When Not To Use

- Do not consult a peer before reading the relevant repo files, logs, tests, or docs locally.
- Do not use a peer call to avoid making a grounded local decision.
- Do not send secrets, tokens, credentials, private keys, customer data, proprietary incident details, or broad repo dumps.
- Do not grant broad filesystem, network, account, or permission bypass access to an untrusted workspace, browser session, or external upload.
- Do not apply peer output directly without local verification.

## Capability Audit

Run a small audit before selecting a peer. Check command presence and authentication status without printing secrets.

```bash
for cmd in claude codex cursor-agent gemini oracle; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '%s: installed at %s\n' "$cmd" "$(command -v "$cmd")"
    "$cmd" --version 2>/dev/null || true
  else
    printf '%s: not found\n' "$cmd"
  fi
done

claude doctor 2>/dev/null || true
codex doctor --json 2>/dev/null || true
cursor-agent status 2>/dev/null || true
```

Report:
- **host:** current runtime when known, otherwise `unknown`
- **installed peers:** `claude`, `codex`, `cursor-agent`, `gemini`, `oracle`
- **auth:** `verified`, `unverified`, or `not checked`
- **peer skill/plugin surface:** named skill or plugin availability when a named peer workflow is requested, otherwise `not needed`
- **default peer:** selected counterpart and reason
- **limits:** subscription tier, browser access, and cloud-agent access if not directly verified

Treat command presence as `installed`, not authenticated. Do not claim a specific subscription tier unless the tool explicitly reports it or a safe probe succeeds. If a peer has no safe status command, report `auth: not checked` and lower confidence in that peer choice. Do not spend tokens, make network calls, or start a model run just to prove auth unless the user asked for a live probe.

## Peer Capability Boundaries

Skills, plugins, slash commands, agents, and subagents are host-local capabilities. Do not assume a skill available in the parent runtime is installed, callable, or semantically identical inside the peer runtime.

- Before asking a peer to invoke a named skill, plugin, slash command, or subagent workflow, verify that peer's surface with a safe local listing, help command, installed-skill path, or tool-visible evidence.
- If the named workflow is not verified, send a plain prompt that inlines the requested review standard, rubric, or task criteria. Ask the peer to report this as a prompt-only fallback.
- For headless or read-only peer runs, avoid named workflows that require subagents, task tools, file edits, shell access, or interactive orchestration unless the installed peer documents that mode as supported.
- If the user specifically wants the named workflow's full machinery and it is not compatible with the selected headless/read-only wrapper, switch to an interactive visible peer surface or an isolated worktree with the needed permissions.
- Report the capability path actually used: `verified named skill/plugin`, `verified CLI only`, `prompt-only fallback`, or `unavailable`.

## Decision Matrix

| Need | Work Type | Permission Mode | Prefer |
| --- | --- | --- | --- |
| Independent PR/code review after local review | `consult` | `readonly` | Counterpart runtime: Claude from Codex, Codex from Claude. |
| Harsh maintainability critique from the same runtime | Use `v1-deep-review` first | n/a | Phone a friend only when a second runtime is requested. |
| Steelman a plan or decision | `steelman` | `readonly` | Counterpart runtime or browser strong model for product/strategy judgment. |
| Reproduce a bug or verify tests | `verify` | `local-verify` | Coding peer in a trusted local worktree. |
| Offload implementation or cleanup | `delegate` | `isolated-delegate` | Coding peer in a disposable or explicitly trusted worktree. |
| True external deep research | `research` | `external` | ChatGPT Pro Deep Research first when available. |
| Large-context or multimodal packet | `consult` or `research` | `readonly` or `external` | Gemini or browser-mode strong model when available. |
| Cursor subscription should be used | `consult`, `verify`, or `delegate` | Match the work | Cursor Agent locally, or Cursor Cloud Agent for async remote work. |
| Oracle Pro browser consult | `consult` or `research` | `external` | Oracle with explicit browser/Pro dry-run preview. |
| User explicitly names a peer | Match the request | Match the work | Named peer if installed and authenticated. |

## Definitions

| Work Type | Goal | Peer Output |
| --- | --- | --- |
| `consult` | Get critique, risks, hypotheses, or alternatives. | Advisory response with assumptions and verification steps. |
| `verify` | Reproduce, inspect, run tests, or check a diff. | Evidence-backed verdict with commands run and results. |
| `steelman` | Build the strongest opposing case. | Best argument against the current plan plus decision criteria. |
| `delegate` | Offload bounded implementation or research. | Diff, artifact, or report plus validation evidence. |
| `research` | Gather and synthesize external evidence. | Sourced summary or research report with limitations. |

| Permission Mode | Use For | Permission Shape |
| --- | --- | --- |
| `readonly` | critique, steelman, architecture advice, product judgment | Read-only or plan/ask mode by default. |
| `local-verify` | checking a local diff, reproducing a bug, running tests | Full command permissions in a trusted repo/worktree are acceptable. |
| `isolated-delegate` | implementation, broad code cleanup, async agent work | Full permissions only in an isolated worktree, disposable environment, or explicitly trusted workspace. |
| `external` | browser ChatGPT Pro, Oracle, pasted/uploaded packet | No secrets, no credentials, no broad source dump, no write access. |

Permission bypass flags are powerful. Use them deliberately for trusted local coding agents, not for external web sessions or untrusted workspaces. Before any `local-verify` or `isolated-delegate` run with full permissions, record the starting dirty state and require the peer to report final `git status`, files changed, commands run, and validation results.

## Delegation Lifecycle

Long-running delegation needs a visible lifecycle, not just a prompt.

- Give each delegated run a short slug tied to the task, for example `<repo>-<issue>-review` or `<feature>-verify`.
- Record the execution surface before launch: terminal tab, tmux window/session, cloud-agent URL, browser session slug, thread id, or other resume handle.
- Record the isolation boundary: worktree path, branch name, sandbox mode, permission mode, and starting dirty state.
- Prefer visible or resumable execution for `isolated-delegate` work. Do not hide a long-running agent in an untracked background process.
- If the host supports tmux, cmux, named terminal tabs, cloud-agent labels, or session slugs, use those as local supervision aids without making them part of the cross-runtime contract.
- For async work, capture how to reattach, what completion signal to watch, and where the peer should leave its report, patch, branch, or PR link.
- Before consuming the result, reattach or inspect the final surface, read the peer report, inspect any diff, and run local verification.

## Run Supervision

Do not wait on a peer run with no observable contract.

- Before launch, state the run slug, peer, permission mode, output location, completion signal, first-progress deadline, and maximum wait or check-in cadence.
- For background or concurrent local runs, capture stdout, stderr, and a completion sentinel per peer. Keep artifacts in a run-specific scratch directory.
- If there is no output, artifact update, completion signal, or visible progress by the first-progress deadline, inspect the process state, stderr, run directory, and resume handle before deciding what to do next.
- If a peer stalls, either reattach, retry once with a narrower plain prompt, switch to a more reliable peer, or mark that peer `stalled` and continue with completed peer outputs.
- Never report a multi-peer consult as complete without saying which peers completed, which were partial, which stalled, and which suggestions were locally verified.

## Command Templates

Keep this file focused on routing and verification. After selecting the peer and permission mode, read:
- [references/command-templates.md](references/command-templates.md) for Claude Code, Codex, Cursor Agent, and Gemini CLI templates.
- [references/oracle-browser.md](references/oracle-browser.md) for Oracle browser review and ChatGPT Pro Deep Research packets.

Invariant: ask every peer to return status, capability path actually used, assumptions, model requested and actual model used when available, execution surface or resume handle when available, evidence, commands run, files changed, dirty state, risks, and local verification steps when the peer can touch the worktree.

## Context Packaging Rules

- Start with the exact decision, failure mode, review target, or delegated task.
- Include the smallest useful file set, diff excerpt, logs, command output, screenshot, artifact, or research packet.
- Prefer file paths plus short excerpts over whole files when the peer does not need full source.
- Redact secrets, tokens, customer names, private URLs, account IDs, and proprietary incident details before sending context.
- For external/browser packets, run a privacy scan over the selected excerpts before upload or paste when feasible.
- Keep project-specific instructions out unless they directly change the answer.
- Ask for JSON or another explicit schema when automation will consume the peer output.
- Ask the peer to label assumptions and uncertainty instead of sounding decisive with thin evidence.
- Include enough local context for the peer to avoid generic advice: repo conventions, acceptance criteria, relevant tests, and known constraints.

## Mechanics

Peer invocation is a child process or external workflow, not shared consciousness.

- The peer sees the prompt, current working directory, files/tools it can access, and any context explicitly packaged.
- The peer does not automatically see the parent conversation, hidden reasoning, or full session logs. Include a concise transcript summary when prior conversation matters.
- The parent can wait for a final response or parse streamed events when the CLI supports JSON/stream JSON.
- The parent should save or summarize peer output when it materially affects decisions.
- File edits made by a full-permission peer are visible through the shared worktree; browser-only or cloud-agent work may require copying back a report, patch, branch, or PR link.

## Model And Effort Selection

Choose the model and reasoning level from task risk, not habit.

Do not hardcode concrete model names in reusable skill instructions. Resolve the current model from local CLI help, model lists, config, or the user's explicit request, then pass that model explicitly for serious work. If the peer does not reveal the actual model used, report `model: not reported`.

| Task | Default |
| --- | --- |
| Quick sanity check | Default or auto model, normal effort. |
| Serious code review | Strongest available coding model, high reasoning. |
| Architecture, security, or migration risk | Strongest available model, high/max reasoning, structured findings. |
| Deep external research | ChatGPT Pro Deep Research first when available. |
| Large-context or multimodal review | Gemini or browser-mode strong model when available. |
| Delegated implementation | Coding-strong model, full permissions in isolated/trusted worktree, mandatory validation evidence. |
| Repeated cheap checks | Lower-cost model is acceptable if the result is locally verified. |

## Verification Rule

Treat peer output as an input to the local investigation, not as authority.

Before acting on advice:
- Re-read the cited local files or evidence.
- Check whether the recommendation fits the repo's contracts and conventions.
- Run the smallest relevant test, lint, typecheck, reproduction, trace, or diff inspection.
- Keep the fix scoped to locally verified facts.
- Inspect any peer-made diff before keeping it.
- Report which peer suggestions were used, ignored, or still unverified when the consult materially influenced the result.

## Reference Files

- **[references/command-templates.md](references/command-templates.md)** - Coding-agent prompt bodies and command wrappers for Claude Code, Codex, Cursor Agent, and Gemini CLI.
- **[references/oracle-browser.md](references/oracle-browser.md)** - External Oracle/browser-mode consults, manual packets, and ChatGPT Pro Deep Research packet format.
