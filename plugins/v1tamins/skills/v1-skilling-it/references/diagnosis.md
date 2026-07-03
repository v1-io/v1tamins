# Diagnosing Skills

A shared vocabulary for *reviewing* an existing skill, not just building a new
one. Each named failure mode has an observable symptom and a specific cure — so
a review says "this is sprawl, disclose it" instead of "this feels long," and
two reviewers settle a dispute by naming the concept rather than trading taste.

## Contents
- [Root virtue: predictability](#root-virtue-predictability)
- [Symptom → failure mode → cure](#symptom--failure-mode--cure)
- [The two loads](#the-two-loads)
- [Leading words](#leading-words)
- [Completion criterion: clarity vs demand](#completion-criterion-clarity-vs-demand)
- [When to split](#when-to-split)
- [Failure modes in full](#failure-modes-in-full)

## Root virtue: predictability

A skill exists to wrangle determinism out of a stochastic system. The root
virtue is **predictability** — the agent taking the same *process* every run,
not producing the same output (a brainstorming skill should *predictably*
diverge; its tokens vary, its behaviour doesn't). Every lever below serves it;
cost and maintainability are symptoms of predictability, not rivals to it.

## Symptom → failure mode → cure

| Symptom you can observe | Failure mode | Cure |
|---|---|---|
| A line the model would already obey by default ("be thorough") | **no-op** | Delete it, or replace a weak leading word with a stronger one ("relentless"). Settle "is this a no-op?" by running the skill, not by debate — it's model-relative. |
| The same meaning stated in two or more places | **duplication** | Keep one **single source of truth**; collapse the copies. Repetition also inflates that meaning's apparent importance. |
| Stale layers nobody removed, because adding felt safe and removing felt risky | **sediment** | A pruning discipline: check each line for **relevance** (does it still bear on the task?) and delete what has gone stale. |
| Simply too long — even when every line is live and unique | **sprawl** | The ladder: disclose reference behind context pointers, and split by branch or sequence so each path carries only what it needs. |
| The agent ends a step early, attention slipping to "being done" | **premature completion** | Sharpen the completion criterion first (cheap, local); only if it's irreducibly fuzzy *and* you observe the rush, hide the later steps by splitting across a real context boundary. |
| A must-have file the agent reaches only sometimes | weak **context pointer** | Fix the pointer's *wording* first (its wording, not its target, decides reach); inline the material only if sharpening fails. |
| A description sits in the window every turn, but the skill only ever fires by hand | needless **context load** | Make it user-invoked (strip the description to a human-facing one-liner) and list it in the router. |
| A pile of user-invoked skills nobody can remember | **cognitive load** | A **router skill** that names each and when to reach for it (v1tamins: `v1-menu`). |

## The two loads

Every skill pays one of two costs, and the choice of which is the invocation decision:

- **Context load** — a **model-invoked** skill keeps its `description` in the window every turn, spending tokens and attention. The agent can reach it autonomously and other skills can reach it. The brake on splitting into more model-invoked skills.
- **Cognitive load** — a **user-invoked** skill (`disable-model-invocation: true`) strips its description; only the human, typing its name, can reach it. Zero context load, but *the human is now the index* that must remember it exists. Not a cost to minimise — it's the price of human agency; spend it where human judgement matters.

Pick model-invocation only when the agent must reach the skill on its own, or another skill must. When user-invoked skills multiply past memory, the cure is a **router skill**. (This is the axis the v1tamins invocation-posture taxonomy encodes: `implicit` / `selective_implicit` / `explicit_only`.)

## Leading words

A **leading word** is a compact concept already in the model's pretraining that the agent thinks *with* while running the skill (e.g. *lesson*, *fog of war*, *tracer bullets*, *tight*, *red*). Used as a repeated token — never restated as a sentence — it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens, by recruiting priors the model already holds.

It earns its keep twice: in the body it anchors *execution* (same behaviour every time the word appears); in the `description` it anchors *invocation* (when the same word lives in your prompts, docs, and code, the agent links it to the skill and fires more reliably).

Actively refactor restated prose into one:
- "fast, deterministic, low-overhead" → *tight* (a *tight* loop).
- "a loop you believe in" → *red* (the loop goes *red* on the bug, or it doesn't — a fuzzy gate becomes a binary observable).

A leading word too weak to beat the default is a **no-op**; the fix is a stronger word, not more prose. Prefer an existing pretrained word — a coined word recruits no priors and costs definition tokens.

## Completion criterion: clarity vs demand

Every step ends on a **completion criterion**, and it has two independent axes:

- **Clarity** — can the agent tell done from not-done? A checkable bound ("every modified model accounted for") resists **premature completion**; a vague one ("understanding reached") invites it. This axis needs *steps* to bite (premature completion is a between-steps failure).
- **Demand** — how much the criterion requires. "Every rule applied" drives thorough **legwork** where "produce a change list" does not. This axis is *not* step-bound: it binds a flat body of reference too, which is how a stepless skill (a review that is all reference) still forces exhaustive work.

The strongest criteria are both checkable and exhaustive. A skill's demand is often carried by a leading word (*comprehensive*, *relentless*) as much as by an explicit bound.

## When to split

Granularity spends one of the two loads, so split only when the cut earns it:

- **By invocation** — split off a model-invoked skill only for a distinct **leading word** that should trigger it on its own, or when another skill must reach it. You pay permanent **context load** for the new always-loaded description, so the independent reach has to be worth it.
- **By sequence** — split a run of **steps** only when the steps still ahead tempt the agent to rush the one in front of it (**premature completion**). Hiding them works only across a *real context boundary* (a user-invoked hand-off or a subagent dispatch); an inline model-invoked call leaves the later steps in context and clears nothing.

## Failure modes in full

- **No-op** — an instruction that changes nothing because the model already does it by default; you pay load to say nothing. Test: does the line change behaviour versus the default? Model-relative, not reader-relative. A line can be perfectly relevant and still be a no-op. (v1tamins' Instruction Value Gate is the same idea with a concrete-form checklist; the no-op test adds the "settle it by running the skill" framing.)
- **Duplication** — the same meaning given more than one home. Costs maintenance and tokens, and inflates a meaning's prominence past its real rank. The accidental inverse of a leading word (which repeats a *token* on purpose, never the meaning).
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline; the slow erosion of relevance.
- **Sprawl** — length itself, whatever its cause — too many lines even when all are live and unique. Distinct from sediment (stale) and duplication (repeated). Cured by the ladder, not by trimming words.
- **Premature completion** — ending a step before it's genuinely done. A tug-of-war between visible post-completion steps (the pull forward) and the completion criterion's clarity (the resistance). Fuzziness is the necessary condition. Defence order: sharpen the bound, then (only if fuzzy and observed) hide later steps by splitting.

## Using this in a review

Name the failure mode, cite the observable symptom, and prescribe the paired cure. Prefer a few high-conviction diagnoses over a long list of nits — the same bar `v1-code-review` and `v1-deep-review` hold.
