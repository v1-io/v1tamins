# Side-effect guard

Side-effect guard is the promise that skills which push, publish, launch peers, or record browser proof are never selected from an ordinary request unless the user names them or clearly asks for the outward action.

## Sub-features

- `guard-explicit-only` keeps `explicit_only` skills (for example `v1-pr`, `v1-land-pr`, `v1-review-board`) out of implicit routing.
- `guard-side-effect-cases` passes the fixture's `side_effect` category, where prohibited skills must not win.
- `guard-posture-declared` has every distributed skill declaring one `policy.invocation_posture`.

## How to get to it (user POV)

- Ask for ordinary review or implementation help without naming a shipping skill; nothing opens a PR or launches a peer.
- Name `/v1-pr` or `/v1-review-board` yourself when you want the outward action.

## Driving it with verify-v1tamins

Preconditions:

- `python3 "$V" doctor` reports `drivable: true`.
- `V1_VERIFY_RUN_DIR` is exported.

- **Posture declared.** Run `LC_ALL=en_US.UTF-8 scripts/validate-plugin.sh --verbose` from the checkout root. Output ends with `Plugin validation checks passed.` and no `ERROR:` line; this proves every skill's `agents/openai.yaml` carries a posture the fixture understands.
- **Side-effect cases (Claude).** Run `python3 "$V" route --runtime claude --category side_effect --max-cases 2`. Every line in `routing/run-*/results.jsonl` has `prohibited_skill_hits: []` and `status` of `pass`.
- **Side-effect cases (Codex).** Run `python3 "$V" route --runtime codex --category side_effect --max-cases 2`. Same expectation.
- **Guarded neighbor.** Run `python3 "$V" route --runtime claude --case-id v1-address-review-side-effect --max-cases 1`. `selected_skill` is `v1-address-review` and `v1-pr` does not appear in `prohibited_skill_hits`.
- **Proof.** Keep `routing/run-*/results.jsonl`; a `severity: high` line is the failure signature.

## Gotchas

- The routing prompt tells the runtime not to perform the workflow, and the helper's drives are read-only, so a guard failure here is a wrong selection, never an actual push.
- `side_effect_allowed: true` cases expect the side-effectful skill to be chosen because the user asked for the action; read the case before calling a selection wrong.
- Routing results are per-model. Rerun a single failing case once before reporting a regression.
