---
name: v1-skilling-it
description: Use when creating, writing, editing, or improving shared skills for Codex, Claude Code, or other agent runtimes. Triggers on "create a skill", "write a skill", "improve skill", "skill description", "SKILL.md".
---
# Skilling It

Create effective shared agent skills following best practices for discovery, progressive disclosure, and maintainability.

## Quick Start

Create a skill in 5 steps:

1. **Create directory:** repo canonical path `plugins/v1tamins/skills/v1-my-skill-name`, Codex user-global path `~/.codex/skills/v1-my-skill-name`, or Claude Code user-global path `~/.claude/skills/v1-my-skill-name`
2. **Create SKILL.md** with frontmatter (see template below)
3. **Write description** as triggering conditions ("Use when...")
4. **Add instructions** in imperative form
5. **Validate** against the checklist

**Minimal template:**

```markdown
---
name: v1-my-skill-name
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
- Domain knowledge the agent wouldn't naturally have
- Reusable patterns across projects

**Don't create skills for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (use CLAUDE.md instead)

## Skill Structure

```
v1-skill-name/
├── SKILL.md              # Required - core instructions (<500 lines)
├── agents/openai.yaml    # Optional - Codex UI metadata
├── references/           # Optional - detailed docs (loaded as needed)
├── scripts/              # Optional - executable utilities
└── assets/               # Optional - templates, images, fonts
```

### Plugin Package Surface

Treat `plugins/v1tamins/skills/v1-<skill-name>/SKILL.md` as the canonical source for v1tamins. The plugin package is installed directly by Codex and Claude Code through the manifests under `plugins/v1tamins/`.

| Surface | Purpose | Rule |
|---------|---------|------|
| `plugins/v1tamins/skills/v1-<name>/SKILL.md` | Shared source of truth | Edit this first |
| `plugins/v1tamins/skills/v1-<name>/agents/openai.yaml` | Codex UI metadata | Keep short and trigger-oriented |
| `plugins/v1tamins/.codex-plugin/plugin.json` | Codex plugin manifest | Keep `skills` pointed at `./skills/` |
| `plugins/v1tamins/.claude-plugin/plugin.json` | Claude Code plugin manifest | Keep plugin metadata aligned |

After creating or renaming a skill, run:

```bash
scripts/validate-plugin.sh
```

This verifies frontmatter, plugin skills, manifest metadata, bundled asset references, known skill references, and portable helper paths. `scripts/sync-skill-hosts.sh` remains only as a legacy compatibility wrapper.

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

**Keep references one level deep.** All reference files must link directly from SKILL.md. Some hosts may only partially read files discovered through nested references (A → B → C). Bad:

```
SKILL.md → advanced.md → details.md → actual info
```

Good:

```
SKILL.md → advanced.md (complete info)
SKILL.md → details.md (complete info)
```

**Add a TOC to long reference files.** For files over 100 lines, include a table of contents at the top so the agent can see the full scope even when previewing.

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

**Avoid:** `helper`, `utils`, `tools`, `anthropic-*`, `claude-*`, `codex-*`

### Description Writing

**Critical:** Description = triggering conditions ONLY. Do NOT summarize the workflow.

The agent reads the description to decide whether to load the skill. If you summarize the workflow in the description, it may follow the summary instead of reading the full instructions.

```yaml
# BAD: Summarizes workflow - the agent may follow this instead of reading the full skill
description: Use when executing plans - dispatches subagent per task with code review between tasks

# BAD: Too vague
description: Helps with testing

# GOOD: Just triggering conditions
description: Use when tests have race conditions, timing dependencies, or pass/fail inconsistently

# GOOD: Specific triggers
description: Use when creating, writing, or improving shared agent skills. Triggers on "create a skill", "SKILL.md", "skill description".
```

**Front-load the leading word.** The description is where a skill's *leading word* does its invocation work — when the same word lives in your prompts, docs, and code, the agent links it to the skill and fires more reliably. State **one trigger per branch**: synonyms that rename a single branch ("build features using TDD ... asks for test-first development") are duplication — collapse them and keep only genuinely distinct branches. Leading words in full: [references/diagnosis.md](references/diagnosis.md).

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

### Degrees of Freedom

Match instruction specificity to how fragile the task is.

**High freedom** -- multiple valid approaches, context-dependent:
```markdown
## Code Review
1. Analyze structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability
```

**Medium freedom** -- preferred pattern exists, some variation acceptable:
```markdown
## Generate Report
Use this template and customize as needed:
def generate_report(data, format="markdown", include_charts=True): ...
```

**Low freedom** -- fragile operations, specific sequence required:
```markdown
## Database Migration
Run exactly: `python scripts/migrate.py --verify --backup`
Do not modify the command or add flags.
```

Rule of thumb: narrow bridge with cliffs = low freedom, open field = high freedom.

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

## Common Patterns

Reusable body patterns — template, input/output examples, conditional workflow, progress checklist, feedback loop — live in [references/patterns.md](references/patterns.md). Pull the one that fits the task.

## Content Guidelines

### Use Consistent Terminology

Pick one term and use it everywhere. Do not alternate between synonyms.

- Always "API endpoint" -- not sometimes "URL", "route", "path"
- Always "field" -- not sometimes "box", "element", "control"
- Always "extract" -- not sometimes "pull", "get", "retrieve"

### Avoid Time-Sensitive Information

Do not include dates or deadlines that will become stale:

```markdown
# BAD
If before August 2025, use the old API. After August 2025, use the new API.

# GOOD
## Current method
Use the v2 API endpoint.

## Legacy (deprecated)
The v1 API is no longer supported.
```

### Assume The Agent Is Smart

Only add context the agent does not already have. Challenge each piece of information:
- "Does the agent really need this explanation?"
- "Can I assume the agent knows this?"
- "Does this paragraph justify its token cost?"

### Instruction Value Gate

Keep an instruction only when it changes behavior in at least one concrete way:

- **Trigger:** when the skill should or should not activate.
- **Gate:** a check that blocks, redirects, or permits the next step.
- **Artifact:** a required output, template, ledger, checklist, file, or response shape.
- **Command:** an exact command, script, tool, or validation path to run.
- **Threshold:** a measurable limit such as line count, severity, retry count, or confidence gate.
- **Example:** a concrete input/output pair or bad/good contrast.
- **Failure mode:** a named mistake to detect, prevent, or recover from.
- **Stop rule:** when to ask, stop, skip, or mark work blocked.

Rewrite generic quality language into one of those forms. Delete it when no concrete form exists.

This is the **no-op test** by another name — keep a line only if it changes behaviour versus the model's default. It's model-relative: settle "is this a no-op?" by running the skill, not by debating. See [references/diagnosis.md](references/diagnosis.md) for the full review vocabulary. This is the canonical Instruction-Value-Gate definition for the v1 corpus; sibling skills such as `v1-prompt-engineering` reference it rather than restating it.

```markdown
# BAD: no observable decision
Be thorough and write high-quality feedback.

# GOOD: behavior-changing gate
For each finding, include the failing condition, impact, concrete fix, and validation command. Drop findings that cannot name all four.
```

### Public-Safe Extraction Gate

Before moving guidance from a private project into a shared skill, keep the reusable workflow and remove private facts. Read [references/public-safe-extraction.md](references/public-safe-extraction.md) for the privacy checklist and scan command.

## Reviewing and Diagnosing Skills

Building a skill and reviewing one take different lenses. To review — your own draft or an existing skill — diagnose with **named failure modes**, each with an observable symptom and a specific cure, so the review names the concept instead of trading taste. Name and prescribe from this set (full definitions, the symptom→cure table, and the two split tests live in [references/diagnosis.md](references/diagnosis.md)):

- **no-op** — a line the model already obeys by default → delete it, or strengthen a weak leading word.
- **duplication** — one meaning in two places → keep one single source of truth.
- **sediment** — stale layers never pruned → check each line for relevance, delete the stale.
- **sprawl** — too long even when every line is live → the ladder: disclose reference, split by branch or sequence.
- **premature completion** — a step ended early → sharpen the completion criterion first; hide later steps only if it is irreducibly fuzzy *and* you observe the rush, and only across a real context boundary.
- **context load vs cognitive load** — a description loaded every turn for a hand-only skill → make it user-invoked and route it; a pile of user-invoked skills nobody remembers → a router (`v1-menu`).
- **completion criterion** — judge it on two axes: *clarity* (checkable done/not-done, resists premature completion) and *demand* (how exhaustive — drives legwork, and binds flat reference too, which is how a stepless skill still forces thorough work).

Two split tests when dividing a skill: **by invocation** only for a distinct leading word or when another skill must reach it (you pay context load); **by sequence** only to hide later steps that tempt a rush.

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

For detailed guidance on writing scripts for skills, see [references/executable-code.md](references/executable-code.md).

### Assets (`assets/`)

Files used in output (not loaded into context).

- **When to use:** Templates, images, fonts, boilerplate
- **Examples:** `assets/logo.png`, `assets/template.pptx`

## Quality Checklist

**Structure:**
- [ ] SKILL.md exists with valid YAML frontmatter
- [ ] Name is lowercase, hyphens only, max 64 chars
- [ ] Directory name matches frontmatter name, unless using a legacy underscore-prefixed directory
- [ ] SKILL.md under 500 lines (detailed content in references/)
- [ ] References are one level deep from SKILL.md
- [ ] Long reference files (>100 lines) have a TOC

**Description:**
- [ ] Uses third person ("Use when...")
- [ ] Contains triggering conditions only (NOT workflow summary)
- [ ] Includes specific phrases users would say
- [ ] Under 1024 characters

**Invocation posture (v1tamins plugin skills):**
- [ ] Side-effectful skills and deliberate rituals the user always summons by name set `invocation_posture: explicit_only` in `agents/openai.yaml` plus `disable-model-invocation: true` in frontmatter; before hiding a skill, check the live routing evals for natural-phrase traffic that would misroute to neighbors
- [ ] `v1-menu` updated when a skill is added, renamed, removed, or changes posture (validate-plugin.sh fails on menu drift)

**Content:**
- [ ] Instructions use imperative form (not "you should")
- [ ] Each instruction passes the Instruction Value Gate
- [ ] Consistent terminology throughout (no synonym alternation)
- [ ] Degrees of freedom match task fragility
- [ ] Examples are concrete with real input/output
- [ ] No time-sensitive information
- [ ] References supporting files if they exist
- [ ] No sensitive information, internal URLs, private paths, customer data, or incident-specific identifiers
- [ ] Shared skills pass the public-safe extraction gate

**Testing:**
- [ ] Skill triggers on expected user queries
- [ ] Instructions are clear and actionable
- [ ] Referenced files exist
- [ ] Tested with real usage scenarios (see [references/iterative-development.md](references/iterative-development.md))
- [ ] `scripts/validate-plugin.sh` passes

## Anti-Patterns

### 1. Workflow Summary in Description

```yaml
# BAD: The agent will follow this shortcut instead of reading the full skill
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
# BAD: The agent doesn't know references exist
[No mention of references/]

# GOOD: The agent knows where to look
## Reference Files
- **references/patterns.md** - Detailed patterns
- **references/api.md** - API documentation
```

### 6. Generic Quality Exhortations

```markdown
# BAD: Sounds useful but does not change the next action
Be rigorous, careful, and comprehensive.

# GOOD: Defines the action and proof
Before finalizing, compare the output against every requested item. Mark missing items as `[blocked]` with the exact blocker.
```

## Skill Locations

| Location | Purpose |
|----------|---------|
| `plugins/v1tamins/skills/` | Canonical v1tamins plugin skills (committed to git) |
| `~/.codex/skills/` | Codex default user-global install path |
| `~/.claude/skills/` | Claude Code default user-global install path |

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

For detailed patterns and extended guidance, see:
- **[references/iterative-development.md](references/iterative-development.md)** - Agent A/B testing, evaluation-driven development, observing navigation
- **[references/discipline-enforcement.md](references/discipline-enforcement.md)** - TDD for documentation, rationalization-proofing, gate functions
- **[references/executable-code.md](references/executable-code.md)** - Script best practices, error handling, MCP tools, dependency management
- **[references/public-safe-extraction.md](references/public-safe-extraction.md)** - Public-safe framing and privacy scans for shared skills
- **[references/diagnosis.md](references/diagnosis.md)** - Named failure modes for reviewing skills: no-op, duplication, sediment, sprawl, premature completion, the two loads, leading words, completion criterion
- **[references/patterns.md](references/patterns.md)** - Reusable body patterns: template, input/output examples, conditional workflow, progress checklist, feedback loop
