# Skill Patterns

Reusable body patterns for `SKILL.md` instructions. Pull the one that fits the
task; not every skill needs any of them.

## Template Pattern

For **strict requirements** (API responses, data formats), enforce exact structure:

````markdown
ALWAYS use this exact template:

```markdown
# [Title]
## Executive summary
[One-paragraph overview]
## Key findings
- Finding with supporting data
```
````

For **flexible guidance** (where adaptation is useful), signal it:

```markdown
Sensible default format -- adjust sections as needed for the analysis type.
```

## Input/Output Examples

Show desired style through concrete pairs rather than descriptions:

````markdown
**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication
Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
```
fix(reports): correct date formatting in timezone conversion
Use UTC timestamps consistently across report generation
```
````

## Conditional Workflow

Guide through decision points when a skill handles multiple task types:

```markdown
1. Determine modification type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing?** → Follow "Editing workflow" below
```

If conditional branches are large, push each into a separate reference file and tell the agent to read the appropriate one.

## Progress Checklist

For complex multi-step workflows, provide a copy-paste checklist the agent can track:

````markdown
Copy this checklist and check off items as you complete them:

```
- [ ] Step 1: Analyze the input
- [ ] Step 2: Create mapping
- [ ] Step 3: Validate mapping
- [ ] Step 4: Apply changes
- [ ] Step 5: Verify output
```
````

## Feedback Loop

For quality-critical operations, build in a validate-fix-repeat cycle:

```markdown
1. Make edits
2. Run validator: `python scripts/validate.py`
3. If validation fails:
   - Review error message
   - Fix the issue
   - Run validation again
4. Only proceed when validation passes
```
