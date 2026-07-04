# Structural Maintainability Rubric

The structural bar for `v1-deep-review`. Apply this as a lens on code changes after the merge-risk passes. The question is not "is it safe to merge?" but **"does this change leave the codebase simpler to change?"** Skip this bar for pure docs/config PRs.

## Review Contract

For every changed area, decide whether the current structure should merge as-is. A structural finding is valid only when it names:

- the concrete structural problem;
- the future change or reader task made harder;
- the simpler ownership, model, module, or flow that should replace it;
- the behavior-preservation check needed after the rewrite.

## Non-Negotiable Standards

1. **Look for structural simplification.** Do not stop at "this could be cleaner." Look for a reframing so whole branches, helpers, modes, conditionals, or layers disappear. If there is a concrete path to delete complexity rather than rearrange it, describe it.
2. **Do not allow random spaghetti growth.** "Weird if statements in random places" is a design problem, not a nit. Prefer pushing logic into a dedicated abstraction, helper, state machine, or module over tangling an existing path. Call out changes that make surrounding code harder to reason about even if they work.
3. **Clean the design, not just accept working code.** If behavior can stay the same while structure gets meaningfully cleaner, push for it. Prefer removing moving pieces over spreading the same complexity around. Do not rubber-stamp "it works" that leaves the codebase messier.
4. **Prefer direct, boring, maintainable code over hacky or magical code.** Flag brittle/ad-hoc/"magic" behavior, generic mechanisms hiding simple data-shape assumptions, and thin/identity/pass-through wrappers that add indirection without clarity.
5. **Push on type and boundary cleanliness when it affects maintainability.** Question unnecessary optionality, `unknown`, `any`, or cast-heavy code where a clearer boundary could exist. Prefer explicit typed models or shared contracts. If a branch relies on silent fallback to paper over an unclear invariant, ask whether the boundary should be explicit.
6. **Keep logic in the canonical layer and reuse existing helpers.** Call out feature logic leaking into shared paths, or implementation details leaking through APIs. Prefer canonical utilities over bespoke one-offs. Push code toward the right package/service/module instead of normalizing drift.
7. **Treat unnecessary sequential orchestration and non-atomic updates as design smells** when the cleaner structure is obvious. Flag serialized independent work and updates that can leave state half-applied — without over-indexing on micro-optimizations.
8. **Prefer a few deep modules over many shallow ones.** Question new modules whose interface is complex relative to what they hide. Prefer deep modules with a simple interface. Look to combine shallow modules into one deep module.
9. **Define errors out of existence.** Flag error-handling branches that exist because ownership, validation, or state modeling is unclear. Classes that expose many exceptions have complex, shallow interfaces. Recommend structural changes that handle errors internally instead of exposing them.

## Primary Questions

For every meaningful change: Is there a "code judo" move that makes this dramatically simpler? Can it be reframed so fewer concepts/branches/layers are needed? Does it improve or worsen local architecture? Did it add branching where a better abstraction should exist? Did a cohesive module become more coupled/stateful/harder to scan? Is the logic in the right file and layer? Did the diff push a file past a healthy size boundary? Do repeated conditionals signal a missing model? Is the abstraction earning its keep, or is it a wrapper? Did the diff add casts/optionality/ad-hoc shapes that obscure the invariant? Is orchestration more sequential or less atomic than it needs to be?

## Flag Aggressively

A complicated implementation where a cleaner reframing could delete whole categories of complexity; refactors that move code without reducing concepts a reader must hold; a file crossing 1000 lines due to the PR (especially if new code could split out); new conditionals bolted onto unrelated paths; one-off booleans/nullable modes/flags complicating control flow; feature-specific logic leaking into general modules; generic "magic" handling; thin/identity wrappers; unnecessary casts/`any`/`unknown`/optionals; copy-pasted logic instead of extracted helpers; narrow edge-case handling buried mid-function; refactors that pass tests but reduce modularity/readability; "temporary" branching likely to become permanent; bespoke helpers where a canonical utility exists; logic in the wrong layer; sequential async where independent work could stay simpler in parallel; partial-update logic leaving state non-atomic.

## Preferred Remedies

Delete a layer of indirection rather than polish it; reframe the state model so conditionals disappear; change the ownership boundary so the feature becomes a natural extension of an existing abstraction; turn special-case logic into a simpler default flow; extract a helper or pure function; split a large file into focused modules; move feature-specific logic behind a dedicated abstraction; replace condition chains with a typed model or dispatcher; separate orchestration from business logic; collapse duplicate branches; delete wrappers that don't clarify the API; reuse the canonical helper; make type boundaries explicit so control flow simplifies; move logic to the module that owns the concept; parallelize independent work when it also simplifies orchestration; restructure related updates into a more atomic flow.

Do not settle for "maybe rename this" when the issue is structural, or for a cleaner version of the same messy idea when a much simpler idea is plausible.

## Structural Finding Shape

```markdown
[Severity] file_path:line_number - Short title
Structural problem: What concept, branch, boundary, file, or abstraction got worse.
Change cost: What future change or reader task becomes harder.
Rewrite path: The smaller ownership/model/module/flow to use instead.
Proof: Test, diff check, or behavior-preservation command that should pass after the rewrite.
```

Prioritize: (1) structural regressions, (2) missed dramatic-simplification / code-judo, (3) spaghetti/branching growth, (4) boundary/abstraction/type-contract problems, (5) file-size/decomposition, (6) modularity, (7) legibility. Prefer a few high-conviction comments over a long list of nits.

## Structural Approval Bar

Do not approve merely because behavior seems correct. Presumptive blockers unless the author justifies them: preserving a lot of incidental complexity when a code-judo move would delete it; pushing a file from below to above 1000 lines; ad-hoc branching that tangles an existing flow; scattering feature checks across shared code; an unnecessary abstraction/wrapper/cast-heavy contract; duplicating an existing helper or putting logic in the wrong layer. If unmet, leave explicit, actionable feedback and push for a cleaner decomposition.

## Tone

Direct technical language. Do not soften major maintainability issues into mild suggestions. If the code makes the codebase messier, say so. If it missed a dramatic simplification, say that too. Example phrasings: `this pushes the file past 1k lines — can we decompose first?`; `this adds another special-case branch into an already busy flow — can we move it behind its own abstraction?`; `this works but makes the surrounding code more spaghetti; keep the behavior, restructure the implementation`; `there's a code-judo move here that makes this much simpler — can we reframe so these branches disappear?`
