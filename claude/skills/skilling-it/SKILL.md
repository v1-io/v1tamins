---
name: skilling-it
description: Use when creating, writing, editing, or improving Claude Code skills. Covers SKILL.md structure, frontmatter, description optimization, progressive disclosure, bundled resources, and validation. Triggers on "create a skill", "write a skill", "improve skill", "skill description", "SKILL.md".
---

# Skilling It

Create effective Claude Code skills following best practices for discovery, progressive disclosure, and maintainability.

## Quick Start

Create a skill in 5 steps:

1. **Create directory:** `mkdir -p ~/.claude/skills/my-skill-name`
2. **Create SKILL.md** with frontmatter (see template below)
3. **Write description** as triggering conditions ("Use when...")
4. **Add instructions** in imperative form
5. **Validate** against the checklist

**Minimal template:**

```markdown
---
name: my-skill-name
description: Use when [triggering condition 1], [triggering condition 2]. Triggers on "[phrase 1]", "[phrase 2]".
---

# My Skill Name

## Quick Start
[Fastest path to value]

## Instructions
[Core guidance]

## Examples
[Concrete usage]
```

## When to Use

Create a skill when you have:
- Non-obvious solutions worth preserving
- Workflows that require specific steps
- Domain knowledge Claude wouldn't naturally have
- Reusable patterns across projects

**Don't create skills for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (use CLAUDE.md instead)

## Skill Structure

```
skill-name/
├── SKILL.md              # Required - core instructions (<500 lines)
├── references/           # Optional - detailed docs (loaded as needed)
├── scripts/              # Optional - executable utilities
└── assets/               # Optional - templates, images, fonts
```

### Progressive Disclosure

Skills load in three levels:

| Level | What Loads | When | Size Target |
|-------|------------|------|-------------|
| 1. Metadata | name + description | Always | ~100 words |
| 2. SKILL.md body | Core instructions | Skill triggers | <500 lines |
| 3. Bundled resources | References, scripts | As needed | Unlimited |

**Keep SKILL.md lean.** Move detailed content to `references/`:
- Detailed patterns → `references/patterns.md`
- API documentation → `references/api.md`
- Extended examples → `references/examples.md`

## Frontmatter

```yaml
---
name: processing-pdfs          # lowercase, hyphens only, max 64 chars
description: Use when...       # triggering conditions only, max 1024 chars
allowed-tools: Read, Grep      # optional: restrict tool access
---
```

### Naming Conventions

Use **gerund form** (verb + -ing):
- `processing-pdfs` not `pdf-processor`
- `debugging-tests` not `test-debugger`
- `creating-skills` not `skill-creation`

**Avoid:** `helper`, `utils`, `tools`, `anthropic-*`, `claude-*`

### Description Writing (CSO)

**Critical:** Description = triggering conditions ONLY. Do NOT summarize the workflow.

Claude reads the description to decide whether to load the skill. If you summarize the workflow in the description, Claude may follow the summary instead of reading the full instructions.

```yaml
# BAD: Summarizes workflow - Claude may follow this instead of reading skill
description: Use when executing plans - dispatches subagent per task with code review between tasks

# BAD: Too vague
description: Helps with testing

# GOOD: Just triggering conditions
description: Use when tests have race conditions, timing dependencies, or pass/fail inconsistently

# GOOD: Specific triggers
description: Use when creating, writing, or improving Claude Code skills. Triggers on "create a skill", "SKILL.md", "skill description".
```

**Format:** Third person, starts with "Use when..."
**Include:** Specific symptoms, error messages, exact user phrases
**Max length:** 1024 characters (aim for <500)

## Instructions Body

Write in **imperative form** (verb-first), not second person:

```markdown
# GOOD: Imperative
Validate the input before processing.
Use the grep tool to search for patterns.

# BAD: Second person
You should validate the input.
You can use the grep tool.
```

### Recommended Sections

```markdown
# Skill Name

## Quick Start
[Immediate actionable example]

## Instructions
[Step-by-step guidance]

## Examples
[Concrete input/output pairs]

## Guidelines
[Rules and constraints]

## Reference Files
[Links to bundled resources]
```

## Bundled Resources

### References (`references/`)

Documentation loaded into context as needed.

- **When to use:** Detailed patterns, API docs, extended examples
- **Best practice:** If >10k words, include grep patterns in SKILL.md
- **Avoid duplication:** Information lives in SKILL.md OR references, not both

### Scripts (`scripts/`)

Executable code for deterministic or repetitive tasks.

- **When to use:** Code that would be rewritten repeatedly
- **Benefits:** Token-efficient, can execute without loading into context
- **Note:** May need to be read for patching or environment adjustments

### Assets (`assets/`)

Files used in output (not loaded into context).

- **When to use:** Templates, images, fonts, boilerplate
- **Examples:** `assets/logo.png`, `assets/template.pptx`

## Quality Checklist

**Structure:**
- [ ] SKILL.md exists with valid YAML frontmatter
- [ ] Name is lowercase, hyphens only, max 64 chars
- [ ] Directory name matches frontmatter name
- [ ] SKILL.md under 500 lines (detailed content in references/)

**Description:**
- [ ] Uses third person ("Use when...")
- [ ] Contains triggering conditions only (NOT workflow summary)
- [ ] Includes specific phrases users would say
- [ ] Under 1024 characters

**Content:**
- [ ] Instructions use imperative form (not "you should")
- [ ] Examples are concrete with real input/output
- [ ] References supporting files if they exist
- [ ] No sensitive information (credentials, internal URLs)

**Testing:**
- [ ] Skill triggers on expected user queries
- [ ] Instructions are clear and actionable
- [ ] Referenced files exist

## Anti-Patterns

### 1. Workflow Summary in Description

```yaml
# BAD: Claude will follow this shortcut instead of reading full skill
description: Use for TDD - write test first, watch it fail, write minimal code, refactor
```

### 2. Everything in SKILL.md

```
# BAD: 8,000 words in one file
skill-name/
└── SKILL.md  (bloated)

# GOOD: Progressive disclosure
skill-name/
├── SKILL.md  (1,800 words)
└── references/
    ├── patterns.md (2,500 words)
    └── advanced.md (3,700 words)
```

### 3. Vague Descriptions

```yaml
# BAD: Won't trigger correctly
description: Helps with documents

# GOOD: Specific triggers
description: Use when extracting text from PDFs, filling PDF forms, or merging documents. Triggers on "PDF", "form filling", "document extraction".
```

### 4. Second Person Instructions

```markdown
# BAD
You should start by reading the file.

# GOOD
Start by reading the file.
```

### 5. Missing Resource References

```markdown
# BAD: Claude doesn't know references exist
[No mention of references/]

# GOOD: Claude knows where to look
## Reference Files
- **references/patterns.md** - Detailed patterns
- **references/api.md** - API documentation
```

## Skill Locations

| Location | Purpose |
|----------|---------|
| `~/.claude/skills/` | Personal skills (user-wide) |
| `.claude/skills/` | Project skills (committed to git) |
| `~/Development/.claude/skills/` | Development/experimental skills |

## Troubleshooting

**Skill doesn't trigger:**
1. Check description includes specific phrases users say
2. Verify frontmatter YAML is valid (no tabs, proper indentation)
3. Add more trigger words to description

**Multiple skills conflict:**
- Make descriptions more distinct
- Use different trigger phrases
- Narrow each skill's scope

**Skill too large:**
- Move detailed content to `references/`
- Keep SKILL.md under 500 lines
- Use progressive disclosure

## Reference Files

For advanced patterns and detailed examples, see:
- **[references/advanced.md](references/advanced.md)** - Testing skills, TDD for documentation, discipline-enforcing patterns
