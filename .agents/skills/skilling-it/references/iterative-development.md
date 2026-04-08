# Iterative Skill Development

## Contents
- [Claude A/B development pattern](#claude-ab-development-pattern)
- [Evaluation-driven development](#evaluation-driven-development)
- [Observing how Claude navigates skills](#observing-how-claude-navigates-skills)
- [Gathering team feedback](#gathering-team-feedback)

## Claude A/B Development Pattern

Use two Claude instances to develop skills effectively:
- **Claude A** (author): Helps design and refine the skill
- **Claude B** (tester): Fresh instance that uses the skill on real tasks

### Creating a New Skill

1. **Complete a task without a skill.** Work through a problem with Claude A using normal prompting. Notice what context you repeatedly provide -- table names, field definitions, filtering rules, query patterns.

2. **Identify the reusable pattern.** After completing the task, identify what context would be useful for similar future tasks.

3. **Ask Claude A to create a skill.** "Create a skill that captures this pattern we just used. Include the schemas, naming conventions, and the filtering rule." Claude understands the skill format natively -- no special prompting needed.

4. **Review for conciseness.** Check that Claude A hasn't over-explained. Ask: "Remove the explanation about what win rate means -- Claude already knows that."

5. **Improve information architecture.** Ask Claude A to organize content. "Move the table schema to a separate reference file. We might add more tables later."

6. **Test with Claude B.** Use the skill with a fresh instance on related use cases. Observe whether Claude B finds the right information and applies rules correctly.

7. **Iterate based on observation.** If Claude B struggles, return to Claude A with specifics: "When Claude used this skill, it forgot to filter by date for Q4. Should we add a section about date filtering patterns?"

### Iterating on Existing Skills

Alternate between:
- **Working with Claude A** to refine the skill
- **Testing with Claude B** on real tasks
- **Observing Claude B's behavior** and bringing insights back to Claude A

1. Give Claude B actual tasks, not test scenarios
2. Note where it struggles, succeeds, or makes unexpected choices
3. Return to Claude A: "Claude B forgot to filter test accounts. The skill mentions it but maybe it's not prominent enough?"
4. Apply Claude A's refinements, test again with Claude B
5. Repeat as new scenarios emerge

## Evaluation-Driven Development

Create evaluations BEFORE writing extensive documentation. This ensures the skill solves real problems rather than documenting imagined ones.

1. **Identify gaps**: Run Claude on representative tasks without a skill. Document specific failures.
2. **Create evaluations**: Build 3+ scenarios that test these gaps.
3. **Establish baseline**: Measure performance without the skill.
4. **Write minimal instructions**: Just enough to address the gaps and pass evaluations.
5. **Iterate**: Execute evaluations, compare against baseline, refine.

Example evaluation structure:

```json
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF and save to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Reads PDF using appropriate library",
    "Extracts text from all pages",
    "Saves to output.txt in readable format"
  ]
}
```

There is no built-in evaluation runner yet. Create your own or use the structure above as a manual testing rubric.

## Observing How Claude Navigates Skills

Watch for these signals as you iterate:

- **Unexpected exploration paths**: Claude reads files in an order you didn't anticipate -- your structure may not be intuitive
- **Missed connections**: Claude fails to follow references to important files -- links need to be more explicit or prominent
- **Overreliance on certain sections**: Claude repeatedly reads the same file -- that content may belong in SKILL.md instead
- **Ignored content**: Claude never accesses a bundled file -- it may be unnecessary or poorly signaled

The `name` and `description` in frontmatter are particularly critical. Claude uses these when deciding whether to trigger the skill. If a skill isn't activating, the description is the first thing to examine.

## Gathering Team Feedback

1. Share skills with teammates and observe their usage
2. Ask: Does the skill activate when expected? Are instructions clear? What's missing?
3. Incorporate feedback to address blind spots in your own usage patterns
