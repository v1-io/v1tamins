---
name: v1-phone-a-friend
description: Use when an agent needs counterpart review, another agent/model consult, steelmanning, delegated implementation, or external strong-model research. Triggers on "phone a friend", "second opinion", "ask another agent", "ask Claude", "ask Codex", "ask Cursor", "ask Oracle", "consult GPT Pro", "steelman this".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - AskUserQuestion
---
# Phone a Friend

Coordinate another agent or model for counterpart review, steelmanning, delegation, deep research, or verification, then validate the result locally.

## Quick Start

1. Inspect the local capability surface before choosing a peer.
2. Default to the strongest available counterpart, not a generic "lane":
   - Running in Codex -> consult Claude Code first.
   - Running in Claude Code -> consult Codex first.
   - Running in Cursor -> consult Claude Code or Codex first, based on availability.
   - Unknown host -> use the best authenticated coding peer that is not the current runtime.
3. Override the counterpart default only when the task has a specialist fit, such as ChatGPT Pro Deep Research, Gemini long-context review, Cursor Agent, or Oracle/browser-mode review.
4. Pick the permission mode for the job: `consult`, `verify`, or `delegate`.
5. Package tight context, run the peer, and locally verify anything that influences the final decision.

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

codex doctor --json 2>/dev/null || true
cursor-agent status 2>/dev/null || true
```

Use the audit to report:

- **host:** current runtime when known, otherwise `unknown`
- **installed peers:** `claude`, `codex`, `cursor-agent`, `gemini`, `oracle`
- **auth:** `verified`, `unverified`, or `not checked`
- **default peer:** selected counterpart and reason
- **limits:** subscription tier, browser access, and cloud-agent access if not directly verified

Do not claim the user has a specific subscription tier unless the tool explicitly reports it or a safe probe succeeds. A local CLI can be installed without the relevant account being authenticated or subscribed.

## Routing Rules

Prefer the counterpart default first. Treat specialty tools as overrides, not generic lanes.

| Situation | Prefer | Why |
| --- | --- | --- |
| Running in Codex | Claude Code | Different model family/runtime gives better independent review of Codex work. |
| Running in Claude Code | Codex | Different model family/runtime gives better independent review of Claude work. |
| Running in Cursor | Claude Code, then Codex | Cursor already owns the current context; use another coding agent first. |
| Host unknown | Best authenticated coding peer not already in use | Avoid self-review when another capable peer exists. |
| User explicitly names a peer | Named peer | User intent overrides the default when the peer is available. |
| True deep web research | ChatGPT Pro Deep Research, then Gemini/Codex/Claude with web access | Specialized research products are better suited than a coding-agent consult. |
| Large-context or multimodal packet | Gemini, then ChatGPT Pro/browser mode | Use the model/tool whose context and media handling match the packet. |
| Cursor subscription should be used | Cursor Agent | Use `cursor-agent` for terminal automation, or Cursor Cloud Agent when the task should run asynchronously in Cursor's remote environment. |
| Strong external/browser review | Oracle or browser-mode ChatGPT Pro / GPT Pro | Use when local CLIs cannot inspect the needed page, upload, or model surface. |

## Work Types

| Work Type | Goal | Peer Output |
| --- | --- | --- |
| `consult` | Get critique, risks, hypotheses, or alternatives. | Advisory response with assumptions and verification steps. |
| `verify` | Reproduce, inspect, run tests, or check a diff. | Evidence-backed verdict with commands run and results. |
| `steelman` | Build the strongest opposing case. | Best argument against the current plan plus decision criteria. |
| `delegate` | Offload bounded implementation or research. | Diff, artifact, or report plus validation evidence. |
| `research` | Gather and synthesize external evidence. | Sourced summary or research report with limitations. |

## Permission Modes

Use the narrowest mode that fits the work, but do not make review agents toothless when the user expects real verification.

| Mode | Use For | Permission Shape |
| --- | --- | --- |
| `consult` | critique, steelman, architecture advice, product judgment | Read-only by default. |
| `verify` | checking a local diff, reproducing a bug, running tests | Full command permissions in a trusted repo/worktree are acceptable. |
| `delegate` | implementation, broad code cleanup, async agent work | Full permissions only in an isolated worktree, disposable environment, or explicitly trusted workspace. |
| `external` | browser ChatGPT Pro, Oracle, pasted/uploaded packet | No secrets, no credentials, no broad source dump, no write access. |

Permission bypass flags are powerful. Use them deliberately for trusted local coding agents, not for external web sessions or untrusted workspaces.

## Command Templates

Adapt exact flags to the installed CLI version. Prefer `stream-json` or JSON output when the parent agent needs progress events or machine-readable parsing.

### Claude Code Counterpart

```bash
claude -p \
  --permission-mode bypassPermissions \
  --output-format stream-json \
  --model <model-or-alias> \
  --effort high \
  "$(cat <<'PROMPT'
Act as an independent counterpart reviewer. You may inspect the repo and run validation commands.
Do not commit, push, publish, send messages, or mutate external services.

Problem:
<one-paragraph problem statement>

Context files:
- <path>
- <path>

Question:
<specific question for critique, risks, hypotheses, or alternatives>

Return:
- Recommendation
- Evidence or assumptions
- Commands run and results
- Risks, missing checks, and local verification steps
PROMPT
)"
```

For a read-only consult, replace the permission mode with allowed/disallowed tools:

```bash
claude -p \
  --allowedTools "Read,Grep,Glob" \
  --disallowedTools "Edit,Write,Bash" \
  "<bounded consult prompt>"
```

### Codex Counterpart

```bash
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --cd <repo> \
  --json \
  --model <model> \
  "$(cat <<'PROMPT'
Act as an independent counterpart reviewer. You may inspect the repo and run validation commands.
Do not commit, push, publish, send messages, or mutate external services.

Problem:
<one-paragraph problem statement>

Context files:
- <path>
- <path>

Question:
<specific question for critique, risks, hypotheses, or alternatives>

Return:
- Recommendation
- Evidence or assumptions
- Commands run and results
- Risks, missing checks, and local verification steps
PROMPT
)"
```

For a read-only consult, use `--sandbox read-only` and ask the peer not to edit or create files.

### Cursor Agent

Use Cursor when the user wants to leverage a Cursor subscription, when Cursor Agent is available, or when the current host is not Cursor and Cursor is the best authenticated peer.

```bash
cursor-agent -p \
  --output-format stream-json \
  --model <model-or-auto> \
  --force \
  "$(cat <<'PROMPT'
Act as an independent counterpart reviewer. You may inspect the repo and run validation commands.
Do not commit, push, publish, send messages, or mutate external services.

Problem:
<one-paragraph problem statement>

Context files:
- <path>
- <path>

Question:
<specific review, steelman, verification, or delegation request>

Return:
- Recommendation
- Evidence or assumptions
- Commands run and results
- Risks, missing checks, and local verification steps
PROMPT
)"
```

For a consult-only Cursor call, omit `--force` and explicitly ask for no edits or commands. For async implementation, use Cursor Cloud Agent only when it is configured and the task is safe to run in its remote environment.

### Gemini CLI

Use Gemini when installed and authenticated, especially for large-context, multimodal, or Google-grounded packets. Check `gemini --help` locally before relying on exact flags.

```bash
gemini \
  --model <model> \
  --output-format stream-json \
  -p "$(cat <<'PROMPT'
Act as an independent counterpart reviewer.

Problem:
<one-paragraph problem statement>

Context:
<bounded file list, diff excerpt, artifact, screenshot description, or research packet>

Question:
<specific review, synthesis, or long-context request>

Return:
- Recommendation
- Evidence or assumptions
- Risks, missing checks, and local verification steps
PROMPT
)"
```

### Oracle / Browser-Mode Strong Review

Use the local Oracle command if one exists, or paste the same packet into browser-mode ChatGPT Pro / GPT Pro. Keep the packet sanitized and bounded.

```text
External consult. Do not ask for credentials, private data, or broad source access.

Problem:
<one-paragraph problem statement>

Context:
<small sanitized excerpt, file list, diff summary, screenshot, or artifact>

Question:
<specific question for critique, risks, hypotheses, or alternatives>

Return:
- Recommendation
- Evidence or assumptions
- Risks and missing checks
- Local verification steps
```

### ChatGPT Pro Deep Research

Prefer ChatGPT Pro Deep Research for serious external research when it is available. Prepare a packet instead of asking a coding agent to improvise broad web research.

```text
Deep research request:

Question:
<research question>

Scope:
- Include:
- Exclude:
- Time range or geography:

Context:
<sanitized background, decision being informed, and any uploaded files>

Output:
- Executive summary
- Evidence-backed findings with sources
- Contradictions or uncertainty
- Practical implications for <decision>
- Limitations
```

## Context Packaging Rules

- Start with the exact decision, failure mode, review target, or delegated task.
- Include the smallest useful file set, diff excerpt, logs, command output, screenshot, artifact, or research packet.
- Prefer file paths plus short excerpts over whole files when the peer does not need full source.
- Redact secrets, tokens, customer names, private URLs, account IDs, and proprietary incident details before sending context.
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
