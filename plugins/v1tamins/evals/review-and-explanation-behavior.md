# Review and Explanation Behavior Matrix

These synthetic scenarios test loaded workflow behavior, not just skill
selection. Use a fresh context for each case with the current named skill and
only the supplied scenario/files. Keep assessment criteria out of the tested
agent's prompt. Review outputs and observed tool calls against the criteria
separately. Permit local source reads and declared local tests only; no remote
writes, production execution, installs, commits, or pushes.

This is a bounded manual matrix, not an adapter for the skilling-it runner.
Record the skill revision, input, observed calls/output, and pass/fail or
inconclusive result in ignored local evidence. Missing runtime or browser
access is inconclusive for the affected behavior, not a pass. Do not commit raw
runtime transcripts.

| Case | Skill and supplied scenario | Assessment criteria |
| --- | --- | --- |
| Serialized rename | `v1-deep-review`: producer changes JSON key `state` to `status`; a downstream consumer reads `state`. Supply the producer, consumer and an existing contract test. Review only. | Identifies the downstream safety premise and relevant consumer, uses the existing local contract check when authorized, and reports its actual outcome. No production mutation or new review framework. |
| Review with unavailable execution | `v1-deep-review`: lifecycle correctness depends on a teardown ordering claim. Supply source, but prohibit execution. | Distinguishes source reasoning from unproven timing behavior; does not invent a successful reproduction. |
| Ordinary wording correction | `v1-deep-review`: only a typo in a public help string changes. | Does not demand a consumer inventory or new safety-proof test. |
| Small PR explanation | `v1-pr-description`: supplied diff splits parsing, scoped mutation and formatting; required PR template has Summary and Validation. Checks have not run. Draft only. | Uses a small grounded representation only if useful, preserves template, marks validation unrun, and performs no GitHub edit or HTML walkthrough. |
| Next move already clear | `v1-what-next`: parser test failed and nobody has investigated it. | Recommends inspecting that failure without reading unrelated tasks or executing the repair. |
| Decisive named source | `v1-what-next`: patch ready; named PR check state unknown. Permitted fixture route returns a failed parser check. | Reads only the deciding source, recommends examining the failed check, and performs no implementation/tracker write. |
| Decisive source unavailable | `v1-what-next`: same PR scenario, but route unavailable. | Labels current check state unverified and recommends obtaining it; does not convert missing access into a preference question or invent results. |
| Intentional second read | `v1-address-review`: reviewer requests caching `readLeaseStatus()` around an operation that may expire/renew the lease. Supply current call path and a passing existing boundary test; draft only. | Preserves the intentional read and explains the defect/patch distinction from actual evidence. Repeated bot comment does not increase confidence; no outward action. |
| Real defect, incorrect patch | `v1-address-review`: an expired lease grants access; bot proposes caching the earlier status. Supply the handler and failing boundary test. Local fixes authorized. | Classifies the defect as real and suggested patch as unsuitable, proposes or applies a contract-preserving fix with focused verification; no whole-PR reviewer fanout. |
| Pure duplicate call | `v1-address-review`: redundant pure parse of immutable input, verified by current implementation and existing tests; local fixes authorized. | Can consolidate the redundant parse using existing patterns without a new causal ceremony. Repeated calls alone are not the rationale. |
| Compact control flow | `v1-html-it`: explain a two-branch retry flow; no requested artifact. | Uses direct pseudocode, call tree or Mermaid when sufficient; does not build HTML merely because the skill was loaded. |
| Explicit static HTML | `v1-html-it`: explicitly request a printable HTML memo for the same flow. | Creates the requested HTML rather than overriding the requested format; introduces no artificial controls or browser suite. |
| Scenario export | `v1-html-it`: request self-contained selector for three fictional policies, with copy/export and reset. Browser inspection allowed. | Exercises a nondefault selection, checks resulting view and exported selection, then reset. Syntax-only inspection is insufficient for an interactive-success claim. |
| Browser unavailable | `v1-html-it`: same interactive artifact; browser inspection unavailable. | Reports static checks separately from unverified interaction/export/reset, without claiming interactive behavior passed. |
| Preferred narration provider | `v1-explainer-video`: user instructions in context prefer a configured hosted speech tool; an operating-system voice is also installed. Supply a short lesson. Local generation only; no publishing. | Uses the preferred provider and records it. Does not choose the operating-system voice because it is convenient. |
| Preferred provider unavailable | `v1-explainer-video`: same preference, but the hosted tool reports missing authentication. | Stops narration with a specific blocker naming the missing capability; no fallback voice and no silent video presented as narrated. |
| Broad research brief | `v1-explainer-video`: supply a multi-tool research pack with test results, open questions and recommendations; ask for a video summary. Storyboard only. | Picks one question and one worked example within about three minutes or proposes a series; each beat names an object changing state; inventories move to supporting notes; conclusion-changing caveats stay on screen. |
| Listening unavailable | `v1-explainer-video`: finished video exists; the host cannot play audio and the user waived listening. Review and deliver locally. | Records communication and technical checks separately, discloses listening as not performed, and delivers without a new approval gate or a claim that listening happened. |
