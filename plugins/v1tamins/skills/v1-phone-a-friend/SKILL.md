---
name: v1-phone-a-friend
description: Use when the user explicitly requests phone-a-friend, a counterpart review, steelman, or peer consult. Triggers on /v1-phone-a-friend or $v1-phone-a-friend only.
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - AskUserQuestion
---
# Phone a Friend

Coordinate another agent or model for counterpart review, steelmanning, delegation, deep research, or verification, then validate the result locally. This is an explicit-only launch surface: discovery may propose a peer, but no peer process starts until the user approves the exact candidate.

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

1. Run the dynamic discovery command in [references/model-selection.md](references/model-selection.md); do not launch during discovery.
2. Show the recommended one-peer roster, current CLI/version, model, reasoning level, prompt source/digest, auth policy, launch state, permission, deadline, catalog/model confidence, and alternatives.
3. Wait for explicit selection. API mode, multiple peers, delegation, research, and write-capable permissions require explicit choices in addition to the skill invocation. If the user has not selected a candidate, return `confirmation_required` and launch zero peers.
4. Package the smallest useful context and remove secrets, private URLs, customer data, tokens, account IDs, and proprietary incident details.
5. Build the command with [scripts/peer_launch.py](scripts/peer_launch.py) rather than by hand, then run exactly that command with [scripts/peer-env.sh](scripts/peer-env.sh) and [scripts/peer-run.sh](scripts/peer-run.sh) and verify the typed result locally.

## Decision Path

1. Use a direct in-agent skill instead when independence is not needed: `v1-deep-review` for in-agent PR review (merge-risk and structural), and `v1-deep-research` for in-agent sourced research.
2. Ask the discovery script for the `quality`, `balanced`, `fast`, or `custom` profile. The recommended default is one read-only counterpart, not a fan-out.
3. Prefer a verified subscription-native counterpart with a current provider catalog and a role fit; use model-family diversity only when more than one peer was explicitly requested.
4. Override the recommendation only after showing the user the current alternatives: a named peer, ChatGPT Pro Deep Research, Antigravity/Gemini large-context or multimodal review, Cursor Agent/Cloud Agent, or Oracle/browser-mode review.
5. Use the decision matrix to pick one work type and one permission mode, then resolve the prompt/rubric source and digest.
6. Load the relevant reference file and run one bounded template. A failed or uncertain dispatch stops that branch; it does not auto-retry or replace the peer.

## When To Use

- Use after producing a plan, diagnosis, implementation, PR description, or review that needs independent scrutiny.
- Use to steelman the best opposing argument before committing to an approach.
- Use to delegate a bounded implementation or research task to another subscribed agent when the result can be checked locally.
- Use when a specialist model/tool is materially better suited: ChatGPT Pro for true deep research, Antigravity CLI (`agy`) for Gemini-backed large-context or multimodal packet review, Cursor for Cursor Agent or IDE-context workflows, Oracle/browser mode for strong external review.
- Use before a risky change when an outside critique could expose missing tests, contract breaks, simpler options, or hidden assumptions.

## When Not To Use

- Do not consult a peer before reading the relevant repo files, logs, tests, or docs locally.
- Do not use a peer call to avoid making a grounded local decision.
- Do not send secrets, tokens, credentials, private keys, customer data, proprietary incident details, or broad repo dumps.
- Do not grant broad filesystem, network, account, or permission bypass access to an untrusted workspace, browser session, or external upload.
- Do not apply peer output directly without local verification.

## Capability Audit

Run the bundled discovery before selecting a peer. It checks command presence, versions, current model catalogs, reasoning levels, and auth policy without printing secrets. In `subscription_native` mode, unset ambient API-key variables first (or run `eval "$(python3 "$PEER_POLICY" --emit-shell-unset)"`) so discovery matches the scrubbed launch environment; otherwise ambient keys are a visible `blocked_api_key_present` policy block.

```bash
# Resolve helpers from this skill's installed directory, not the project cwd.
PEER_CATALOG="<this skill dir>/scripts/peer_catalog.py"
PEER_POLICY="<this skill dir>/scripts/peer_policy.py"
eval "$(python3 "$PEER_POLICY" --emit-shell-unset)"
python3 "$PEER_CATALOG" \
  --profile quality \
  --auth-mode subscription_native
```

Report:
- **host:** current runtime when known, otherwise `unknown`
- **installed peers:** `claude`, `codex`, `cursor-agent`, `agy` (Antigravity CLI); Oracle remains a manual/browser path outside the discovery allowlist
- **credential policy:** `eligible`, `not_authenticated`, `auth_not_verified`, `blocked_api_key_present`, `explicit_api_mode`, `api_key_required`, or `not_installed`
- **launch state:** derived readiness such as `eligible`, `model_unresolved`, or a distinct policy failure
- **model catalog:** `resolved`/`unresolved`, with `verified`/`unresolved` confidence from provider catalog commands only
- **default peer:** proposed counterpart and reason; not yet launched
- **limits:** subscription tier, browser access, and cloud-agent access if not directly verified

Treat command presence as `installed`, not authenticated. Do not claim a specific subscription tier unless the tool explicitly reports it or a safe probe succeeds. A current CLI with no reliable model-list surface is `model_unresolved`; never guess a model. In `subscription_native` mode, an API-key variable being present is a visible policy block, not permission to use it.

The script bounds every provider probe. A timeout becomes `auth_not_verified`/`unresolved` evidence rather than a launch or a replacement-peer trigger. The audit is a quick orientation, never a blocker.

## Peer Capability Boundaries

Skills, plugins, slash commands, agents, and subagents are host-local capabilities. Do not assume a skill available in the parent runtime is installed, callable, or semantically identical inside the peer runtime.

- Before asking a peer to invoke a named skill, plugin, slash command, or subagent workflow, verify that peer's surface with a safe local listing, help command, installed-skill path, or tool-visible evidence.
- If the named workflow is not verified, send a plain prompt that inlines the requested review standard, rubric, or task criteria. Ask the peer to report this as a prompt-only fallback. See [references/command-templates.md](references/command-templates.md) (Inlining a Named Skill's Rubric) for a runtime pattern that resolves a named skill's `SKILL.md` and embeds it, with no committed host path. Mark the prompt source and digest in the proposal.
- For headless or read-only peer runs, avoid named workflows that require subagents, task tools, file edits, shell access, or interactive orchestration unless the installed peer documents that mode as supported.
- If the user specifically wants the named workflow's full machinery and it is not compatible with the selected headless/read-only wrapper, switch to an interactive visible peer surface or an isolated worktree with the needed permissions.
- Report the capability path actually used: `verified named skill/plugin`, `verified CLI only`, `prompt-only fallback`, or `unavailable`. A missing workflow is a typed degradation; do not select a replacement without the user.

## Decision Matrix

| Need | Work Type | Permission Mode | Prefer |
| --- | --- | --- | --- |
| Independent PR/code review after local review | `consult` | `readonly` | Counterpart runtime: Claude from Codex, Codex from Claude. |
| Harsh maintainability critique from the same runtime | Use `v1-deep-review` first | n/a | Phone a friend only when a second runtime is requested. |
| Steelman a plan or decision | `steelman` | `readonly` | Counterpart runtime or browser strong model for product/strategy judgment. |
| Reproduce a bug or verify tests | `verify` | `local-verify` | Coding peer in a trusted local worktree. |
| Offload implementation or cleanup | `delegate` | `isolated-delegate` | Coding peer in a disposable or explicitly trusted worktree. |
| True external deep research | `research` | `external` | ChatGPT Pro Deep Research first when available. |
| Large-context or multimodal packet | `consult` or `research` | `readonly` or `external` | Antigravity CLI (`agy`) or browser-mode strong model when available. |
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

- **Background by default.** Launch any peer that could exceed the host's command timeout as a detached background process — never foreground-`wait` on it. The host's timeout (e.g. an agent's 2-minute Bash default) signals the parent's process group and reaps a peer backgrounded with a bare `&`. Use the bundled `scripts/peer-run.sh` helper, which detaches with `setsid` when available, otherwise Perl `POSIX::setsid`, and only then `nohup`, so a parent-shell timeout does not reap it. On the `nohup` fallback this is best-effort, so pair it with the host's background primitive. See [references/command-templates.md](references/command-templates.md) (Supervised Local Runs).
- Before launch, state the run slug, peer, permission mode, output location, completion signal, first-progress deadline, and maximum wait or check-in cadence.
- For background or concurrent local runs, capture stdout, stderr, and a completion sentinel per peer. Keep artifacts in a run-specific scratch directory.
- **Judge completion by substantive output, not exit code.** A peer that returned real content under a nonzero or unusual exit code is complete; an empty success exit is a stall. Wrapper exit codes are advisory.
- **Tear down by recorded PID only.** Kill a stalled peer by the PID you captured at launch — never a pattern kill like `pkill -f "codex exec"`, which can reap an unrelated peer the user is running elsewhere.
- If there is no output, artifact update, completion signal, or visible progress by the first-progress deadline, inspect the process state, stderr, run directory, and resume handle before deciding what to do next.
- If a peer stalls, inspect its recorded status, stderr, sentinel, and PID. Record the runner lifecycle (`stalled` or `timed_out`) or, when dispatch occurred but evidence is ambiguous, parent-level `execution_uncertain`. Do not retry, switch, or add a peer automatically; ask for a fresh explicit selection if the user wants another attempt.
- **Routing is reliability-aware.** Headless reliability differs by peer and recipe: apply the hardened invocations (stdin closed, `peer-env.sh` subscription scrubbing, streaming output) before sending real work to a peer, and show reliability evidence in the proposal. A stalled peer does not make another peer the silent default.
- Never report a multi-peer consult as complete without saying which peers completed, which were partial, which stalled, and which suggestions were locally verified.

## Quick Consult Express Lane

Not every consult needs a large packet, but even the single-peer express lane runs the discovery/proposal gate and records a deadline. Package the question, wait for explicit selection, run one read-only wrapper with stdin closed, read the typed verdict, and verify locally. Graduate to the full Run Supervision lifecycle when more than one peer is involved, the work is `verify`/`delegate`, or the run could outlast the host's command timeout.

## Command Templates

Keep this file focused on routing and verification. After selecting the peer and permission mode, read:
- [references/command-templates.md](references/command-templates.md) for Claude Code, Codex, Cursor Agent, and Antigravity CLI templates.
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

Load [references/model-selection.md](references/model-selection.md) for the
profiles and candidate contract. `quality` is the opinionated default for a
serious counterpart review: choose the strongest current eligible model and
highest reasoning level that its catalog exposes. `balanced` and `fast` remain
available, and `custom` requires the user to select current values. If the
peer does not reveal the actual model used, report `model: not reported`; do
not treat the requested model as proof of the actual model.

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

- **[scripts/peer_catalog.py](scripts/peer_catalog.py)** - bounded provider/version/model/reasoning/auth discovery and profile proposal; it never launches a model.
- **[scripts/peer-env.sh](scripts/peer-env.sh)** - explicit subscription-native/API credential policy wrapper.
- **[scripts/peer_launch.py](scripts/peer_launch.py)** - per-provider launch adapters; builds the approved argv, refuses unrepresentable selections, and never dispatches.
- **[scripts/peer-run.sh](scripts/peer-run.sh)** - detached, stdin-safe, deadline-bounded lifecycle and typed verdict.
- **[scripts/peer_verdict.py](scripts/peer_verdict.py)** - shape-based terminal-answer classifier behind the runner verdict; reports the envelope family.
- **[references/peer-execution-contract.md](references/peer-execution-contract.md)** - typed discovery, auth, selection, execution, and stale-context contract.
- **[references/model-selection.md](references/model-selection.md)** - dynamic profile ranking and current-catalog rules.
- **[references/command-templates.md](references/command-templates.md)** - Coding-agent prompt bodies and command wrappers for Claude Code, Codex, Cursor Agent, and Antigravity CLI.
- **[references/oracle-browser.md](references/oracle-browser.md)** - External Oracle/browser-mode consults, manual packets, and ChatGPT Pro Deep Research packet format.
