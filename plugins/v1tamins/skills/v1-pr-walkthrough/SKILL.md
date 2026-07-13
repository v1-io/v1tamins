---
name: v1-pr-walkthrough
description: Use when explaining a pull request or branch through a browser walkthrough instead of leaving merge-blocking review findings. Triggers on "walk me through this PR", "PR walkthrough", "visual code review", "show touched files", "what changed across files", "execution order".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - Skill
---
# PR Walkthrough

Create a throw-away, self-contained HTML walkthrough that explains what a PR or branch is trying to accomplish, what changed, how touched files relate, and how execution moves through the changed layers.

Use `v1-deep-review` when the requested product is merge-risk or maintainability findings. Use this skill when the requested product is understanding, navigation, or reviewer onboarding.

## Usage

Typical invocations:
- Claude Code: `/v1-pr-walkthrough <PR_URL_or_NUMBER>`
- Claude Code: `/v1-pr-walkthrough` to explain the current branch
- Codex: invoke `v1-pr-walkthrough` from the skills menu or use `$v1-pr-walkthrough <PR_URL_or_NUMBER>`

Examples:
```bash
/v1-pr-walkthrough https://github.com/your-org/your-repo/pull/123
/v1-pr-walkthrough 123
/v1-pr-walkthrough current branch
```

In Codex, the slash examples above map directly to `$v1-pr-walkthrough ...`.

## Workflow

### 1. Resolve The Review Target

Determine whether the target is a GitHub PR or the current branch.

For a PR argument:
```bash
gh pr view <PR> --json number,url,title,body,author,baseRefName,headRefName,headRefOid,commits,files,additions,deletions,labels
gh pr diff <PR> --name-only
gh pr diff <PR> --stat
gh pr diff <PR>
```

For the current branch:
```bash
git status --short
git branch --show-current
BASE_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')"
BASE_BRANCH="${BASE_BRANCH:-main}"
git fetch origin "$BASE_BRANCH"
MERGE_BASE="$(git merge-base "origin/$BASE_BRANCH" HEAD)"
git diff --name-only "$MERGE_BASE"...HEAD
git diff --stat "$MERGE_BASE"...HEAD
git diff "$MERGE_BASE"...HEAD
git log --oneline "$MERGE_BASE"..HEAD
```

If the local checkout does not match the PR head, say so in the artifact and use GitHub metadata plus fetched refs as the source of truth.

Completion criterion: target URL or branch, base/head, changed file list, diff stat, commit list, and raw diff are available or explicitly marked unavailable with the exact blocker.

### 2. Build The Source Ledger

Create a compact ledger before designing the page:

| Item | Evidence to collect |
| --- | --- |
| Intent | PR title/body, commit subjects, branch name, linked ticket text if locally accessible |
| Changed surface | File list, diff stat, packages/modules, generated or vendored files |
| Review context | `AGENTS.md`, `CLAUDE.md`, README, PR template, CODEOWNERS, touched docs |
| Validation | Test files, workflow changes, checks mentioned in PR text, local commands run |
| Unknowns | Missing refs, unavailable ticket systems, generated files not expanded, inaccessible services |

For every touched file, record:
- `role`: what the file does in the repository.
- `change`: what the diff changed in that file.
- `interactions`: imports, callers, callees, runtime contracts, config links, tests, or docs that connect it to the rest of the system.
- `evidence`: paths, symbols, commands, or short diff snippets that support the summary.

Use repo search for every meaningful production symbol, route, component, handler, model, config key, migration, or public helper touched by the diff. Classify lockfiles, generated output, snapshots, docs, tests, and deleted files instead of forcing them into production layers.

Completion criterion: every touched file is classified, every meaningful code file has role/change/interactions/evidence, and every unknown is listed instead of silently skipped.

### 3. Build The Touched-File Table And Connection Flowchart

Create two distinct data models for the HTML page:

```text
touched-file row: file path, layer, role, change summary, connected files, evidence, risk flags
flowchart edge: from file or layer, to file or layer, relationship type, evidence, confidence
```

Layer nodes from highest to lowest applicable level:
- Entry/UI/CLI/job/event surface
- API/route/controller boundary
- Application/service orchestration
- Domain/model/policy logic
- Data/storage/external-service boundary
- Tests/fixtures/tooling/docs

The touched-file map is a **table**, not cards. Make one row per touched file so reviewers can scan paths, roles, changes, interactions, evidence, and risk flags without opening separate blocks.

The connection view is a **visual flowchart**, not a table. Draw imports, calls, request/response contracts, shared types, configuration, data flow, test coverage, or documentation links as arrows or lines between layer/file nodes. Use inline SVG, positioned HTML/CSS, or another self-contained browser-native technique. Label edges with the relationship type, mark inferred edges as inferred, and show isolated files as isolated nodes.

Completion criterion: every touched file appears exactly once in the touched-file table, every meaningful connection appears as a visual flowchart edge or an isolation note, and each edge has evidence or is marked inferred. A connection-edge table alone does not satisfy this step.

### 4. Walk Layers In Execution Order

Identify the primary execution path the PR changes. If the diff changes multiple independent paths, make one primary path and add secondary lanes.

For each layer, write:
- Purpose: why this layer exists in the flow.
- Files: touched files in this layer.
- Changed behavior: what now happens differently.
- Contract: what this layer receives from the layer above and passes down.
- Interaction: which untouched code, services, data, config, or tests it depends on.
- PR snippet: a small changed-code excerpt from the most representative touched file in this layer, with file path and line numbers when available.
- Reviewer focus: questions or risks a reviewer should inspect.

Start at the highest user-visible or runtime entry point and move down through execution order. For docs-only, test-only, or tooling-only changes, replace runtime execution with the actual reader/test/tool execution sequence.

Keep snippets short enough to scan, usually 5-20 lines. Prefer changed lines plus the minimum surrounding context needed to understand the layer. If a layer has no useful changed snippet, state why instead of fabricating one.

Completion criterion: the walkthrough starts at the highest changed entry point, moves downward in execution order, includes a relevant PR snippet or no-snippet reason for each layer, and mentions every changed production file in a layer or explicitly explains why no production layer exists.

### 5. Build The Throw-Away HTML File

Create one self-contained HTML file in `/tmp` by default:

```text
/tmp/pr-walkthrough-<repo-or-pr-slug>.html
```

Use the bundled template and renderer instead of creating the page shell from scratch:

1. Resolve `SKILL_DIR` to the directory containing this `SKILL.md`.
2. Read [references/walkthrough-data.example.json](references/walkthrough-data.example.json) for the required data shape.
3. Write a PR-specific JSON file to `/tmp/pr-walkthrough-<repo-or-pr-slug>.json`. Replace all example values; do not leave example repository names, paths, counts, snippets, or evidence in the output.
4. Keep flowchart node labels at 30 characters or fewer and details at 38 characters or fewer. Assign each node a non-negative `column` and `row` in execution order.
5. Render the artifact:

```bash
python3 "$SKILL_DIR/scripts/render_walkthrough.py" \
  --input "/tmp/pr-walkthrough-<repo-or-pr-slug>.json" \
  --output "/tmp/pr-walkthrough-<repo-or-pr-slug>.html"
```

The renderer validates file/layer/node identities, flowchart edges, edge evidence, and per-layer snippets before writing static semantic HTML. Treat a renderer error as a data error: fix the JSON and rerun it. Do not bypass the validation or hand-author a different page shell.

The bundled template supplies inline CSS and inline JavaScript. It requires no dev server, build step, package install, CDN, or external network request. If the repository has an explicit temporary artifact convention, use it only when it is clearly throw-away and not committed by default.

The first viewport must contain:
- PR or branch title, source, base/head, author when available, and generated timestamp.
- One-sentence intent.
- Changed-file counts by layer and risk flag.
- Primary controls: filter by layer, search file path, expand/collapse all, copy Markdown summary.

The body must contain:
- Overview: what the PR tries to accomplish, what changed, what seems most important to review.
- Touched-file map: a dense table with one row per touched file and columns for layer, role, change, interactions, evidence, and risk flags. Do not render touched files as cards.
- Connection flowchart: a visual flowchart with arrows or lines showing execution/data/config/test relationships between touched files or layers. Do not reduce connection edges to only a table.
- Layer walkthrough: highest layer to lowest layer, in execution order, with a small relevant PR snippet inside each layer.
- Evidence snippets: short excerpts only, with file paths and line numbers where available.
- Unknowns and assumptions: blocked sources, inferred links, generated files, or unverified behavior.
- Provenance: commands and sources used to build the page.

Preserve the template's native controls, visible focus states, internal table/flowchart scrolling, static no-JavaScript content, responsive layout, layer filters, file search, accessible table sorting, flowchart highlighting, collapsible layer details, copy feedback, and source links.

Completion criterion: the HTML opens directly from disk, contains every requested section, has no external dependencies, every touched-file table row links to its layer section, and every flowchart node links to the relevant table row or layer section.

### 6. Validate The Walkthrough

Before responding:
- Check the file exists at the reported path.
- Scan for external URLs in `src=`, `href=`, `script`, `link`, or `import` unless they are explicit source links in provenance.
- Check that every touched file from the diff appears in the touched-file table.
- Check that touched files are rendered as table rows, not cards.
- Check that meaningful connection edges render as a visual flowchart with arrows or lines, not only as a table.
- Check that every production file appears in the layer walkthrough or has an explicit non-runtime classification.
- Check that every layer has a small relevant PR snippet or an explicit no-snippet reason.
- Check that search/filter/copy controls do not throw obvious JavaScript syntax errors.
- Check that table sort controls are keyboard reachable and expose `aria-sort`.
- Check that copy success or failure appears beside the controls through the live status region.
- Check at desktop and mobile widths that the page itself has no horizontal overflow; wide tables, flowcharts, paths, and snippets must scroll or wrap inside their own containers.
- Check that the first viewport contains the title, source, base/head, author, generated timestamp, intent, summary counts, and primary controls.
- When browser automation is available, visually inspect the first viewport, touched-file table, flowchart, and one expanded layer at desktop and mobile widths. Check contrast, clipping, text overlap, focus visibility, and readable code snippets.
- Check that the artifact distinguishes sourced facts, inferences, and unknowns.

If private snippets, secrets, tokens, or credentials appear in the diff, omit the snippet and replace it with a redaction note in the artifact.

Completion criterion: each validation check has passed or is listed in the response with the exact blocker.

## Output

Return a short response:

```markdown
Created: [pr-walkthrough.html](/absolute/path/to/pr-walkthrough.html)

Coverage:
- Files mapped: <n>/<n>
- Layers walked: <top layer> -> <bottom layer>
- Source: <PR URL or branch/base/head>

Validation:
- <checks passed or blockers>
```

Do not post review findings to GitHub from this skill. If the walkthrough reveals merge-blocking issues, mention them as reviewer focus areas and recommend `v1-deep-review` for a findings pass.

## Bundled Resources

- [assets/pr-walkthrough-template.html](assets/pr-walkthrough-template.html) - Accessible, responsive, self-contained artifact shell.
- [scripts/render_walkthrough.py](scripts/render_walkthrough.py) - Standard-library renderer and data validator.
- [references/walkthrough-data.example.json](references/walkthrough-data.example.json) - Public-safe example of the complete input contract.
