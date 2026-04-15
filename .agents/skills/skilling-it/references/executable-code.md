# Executable Code in Skills

## Contents
- [Solve, don't punt](#solve-dont-punt)
- [Document magic numbers](#document-magic-numbers)
- [Verifiable intermediate outputs](#verifiable-intermediate-outputs)
- [Feedback loops in scripts](#feedback-loops-in-scripts)
- [MCP tool references](#mcp-tool-references)
- [Package dependencies](#package-dependencies)
- [Execution vs reading](#execution-vs-reading)

## Solve, Don't Punt

Scripts should handle error conditions rather than failing for Claude to figure out.

**Good -- handle errors explicitly:**
```python
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, "w") as f:
            f.write("")
        return ""
    except PermissionError:
        print(f"Cannot access {path}, using default")
        return ""
```

**Bad -- punt to Claude:**
```python
def process_file(path):
    return open(path).read()  # just fails
```

## Document Magic Numbers

Every constant needs justification. If you don't know the right value, Claude won't either.

```python
# GOOD: Self-documenting
REQUEST_TIMEOUT = 30  # HTTP requests typically complete within 30s
MAX_RETRIES = 3       # Most intermittent failures resolve by second retry

# BAD: Voodoo constants
TIMEOUT = 47  # Why 47?
RETRIES = 5   # Why 5?
```

## Verifiable Intermediate Outputs

For complex operations, use plan-validate-execute to catch errors early.

Instead of: analyze → execute → hope for the best

Use: analyze → **create plan file** → **validate plan** → execute → verify

Example -- updating 50 form fields from a spreadsheet. Without validation, Claude might reference non-existent fields, create conflicting values, or miss required fields. With an intermediate `changes.json`:

```
1. python scripts/analyze_form.py input.pdf > fields.json
2. Create changes.json mapping fields to new values
3. python scripts/validate_fields.py changes.json fields.json  ← catches errors
4. python scripts/fill_form.py input.pdf changes.json output.pdf
5. python scripts/verify_output.py output.pdf
```

**Make validation scripts verbose.** Specific error messages help Claude self-correct:

```
Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed
```

**When to use:** Batch operations, destructive changes, complex validation rules, high-stakes operations.

## Feedback Loops in Scripts

Build validate-fix-repeat cycles into workflows that use scripts:

```markdown
1. Make edits to the document
2. Validate: `python scripts/validate.py output_dir/`
3. If validation fails:
   - Review the error message
   - Fix the issue
   - Run validation again
4. Only proceed when validation passes
5. Rebuild: `python scripts/pack.py output_dir/ output.docx`
```

The validation loop catches errors before they compound into harder problems downstream.

## MCP Tool References

Always use fully qualified names to avoid "tool not found" errors when multiple MCP servers are available.

**Format:** `ServerName:tool_name`

```markdown
# GOOD
Use the BigQuery:bigquery_schema tool to retrieve table schemas.
Use the GitHub:create_issue tool to create issues.

# BAD -- ambiguous when multiple servers are available
Use the bigquery_schema tool.
Use the create_issue tool.
```

## Package Dependencies

List required packages and provide install commands. Do not assume availability.

````markdown
# BAD: Assumes installation
"Use the pdf library to process the file."

# GOOD: Explicit
Install required package: `pip install pypdf`

```python
from pypdf import PdfReader
reader = PdfReader("file.pdf")
```
````

## Execution vs Reading

Make clear whether Claude should execute a script or read it as reference:

```markdown
# Execute (most common -- more reliable and token-efficient)
Run `analyze_form.py` to extract fields.

# Read as reference (for understanding complex logic)
See `analyze_form.py` for the field extraction algorithm.
```

Prefer execution for most utility scripts. Benefits:
- More reliable than generated code
- Saves tokens (no need to include code in context)
- Saves time (no code generation step)
- Ensures consistency across uses
