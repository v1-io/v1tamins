# Interaction Review Taxonomy

Use this reference when a skill needs shared language for interaction review, prototype observation, or user-error diagnosis. Keep the task-specific workflow in the calling skill; use this file for the repeated taxonomy.

## Action Cycle

| Stage | Review Question |
| --- | --- |
| Goal | Is the user's goal supported by this surface? |
| Plan | Can the user tell which path or control might achieve the goal? |
| Specify | Can the user determine the exact action, input, or sequence? |
| Perform | Can the user execute the action with the available controls? |
| Perceive | Does the system make the result visible quickly enough? |
| Interpret | Can the user understand what the result means? |
| Compare | Can the user compare the result to the original goal and decide what to do next? |

Find the gulf of execution when the user cannot tell what to do. Find the gulf of evaluation when the user cannot tell what happened or whether it worked.

## Discoverability Mechanisms

- **Affordances:** possible actions are physically, visually, or conventionally apparent.
- **Signifiers:** actionable elements and unavailable actions are clearly signaled.
- **Mappings:** controls, labels, spatial layout, and outcomes correspond naturally.
- **Feedback:** every meaningful action produces timely, perceivable, interpretable feedback.
- **Constraints:** invalid, dangerous, or impossible actions are prevented or visibly unavailable.
- **Conceptual model:** objects, relationships, state, and scope are visible enough for correct prediction.
- **Knowledge in the world:** needed cues are visible at the moment of use instead of relying on memory.

Do not stop at "make it clearer." Name which mechanism failed and why the user would mispredict the outcome.

## Error Modes

- **Slip:** the user has the right goal but performs the wrong action, selects the wrong item, mistypes, forgets a step, or acts in the wrong mode.
- **Mistake:** the user has the wrong goal, rule, mental model, or interpretation of system state.
- **Mode error:** the same action means different things in different states without strong state visibility.
- **Memory burden:** the user must remember invisible IDs, prior choices, field meanings, keyboard shortcuts, or cross-screen state.
- **Irreversible action:** destructive or costly actions lack confirmation, preview, undo, delay, or recovery.
- **Automation surprise:** the system acts on the user's behalf without showing intent, limits, or handoff points.
- **Extreme input:** forms accept nonsensical values without range checks, units, preview, or plausibility warnings.

Treat mistakes as design evidence before treating them as user failure.

## Fix Priority

Prefer fixes in this order:

1. Prevent invalid actions with constraints, disabled states, range checks, ownership checks, or precondition checks.
2. Make the correct action easier to discover through labels, grouping, mapping, defaults, or visible state.
3. Add timely feedback so users can perceive, interpret, and compare the result against their goal.
4. Add recovery through undo, idempotency, confirmation at the destructive boundary, or safe retry.
5. Add warnings or documentation only when prevention, discoverability, feedback, or recovery cannot reasonably solve it.

## Prototype Observation Row

Use this row shape when observing important prototype tasks:

| Task | Goal Cue | Expected First Action | Feedback Needed | Watch For |
| --- | --- | --- | --- | --- |
| [User goal] | [What tells them where to start] | [Likely action] | [How success/failure/pending should be visible] | [Execution gulf, evaluation gulf, slips, mode errors] |
