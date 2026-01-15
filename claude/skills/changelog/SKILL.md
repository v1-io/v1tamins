---
name: changelog
description: Generate changelog for recent merged PRs
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# Write Changelog

Generate a changelog for recent changes by reviewing merged PRs since the last changelog.

## Usage

```
/changelog
```

## What It Does

1. **Finds Latest Changelog**
   - Checks your changelog directory (e.g., `docs/internal/changelog/` or `$CHANGELOG_DIR`)
   - Identifies most recent changelog by date in filename

2. **Fetches Recent PRs**
   - Uses GitHub API to get all PRs merged to main since last changelog
   - Extracts PR titles, descriptions, and metadata

3. **Generates New Changelog**
   - Creates markdown file with date in filename
   - Formats according to project conventions

## Changelog Format

The changelog follows this structure:

- **1-3 Most Impactful Changes** (heading 2 each)
  - Title: 1-3 words describing the change
  - Description: 1-2 sentences explaining the change
  - Placeholder for visual (screenshot/diagram)

- **Summary of Smaller Changes** (if applicable)
  - High-level bullets for minor updates

## Focus

- **User-facing changes** and new features
- **Breaking changes** highlighted prominently
- **Major bug fixes** and improvements
- Skip internal refactors unless significant

## Example Structure

```markdown
# Changelog - 2026-01-07

## Advanced Filtering

Added support for complex filter expressions in the query interface. Users can now combine multiple conditions using AND/OR operators and apply filters across related tables.

[Placeholder for screenshot]

## Performance Boost

Optimized query execution engine reduces average query time by 60% for large datasets through intelligent caching and parallel processing.

[Placeholder for screenshot]

## Additional Updates

- Fixed authentication timeout issues in Safari
- Improved error messages for failed data source connections
- Updated UI styling for better accessibility
```

## Notes

- Requires GitHub CLI (`gh`) to be installed and authenticated
- Changelog saved to your changelog directory (e.g., `docs/internal/changelog/YYYY-MM-DD.md`)
- Focuses on user impact, not technical implementation details
