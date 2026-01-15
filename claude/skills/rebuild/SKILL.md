---
name: rebuild
description: Trigger rebuild of a specific service in Tilt
allowed-tools:
  - Bash
---

# Rebuild Service

Trigger a rebuild of a specific service in Tilt. Useful after making changes to service code or dependencies.

## Usage

```
/rebuild <service-name>
```

**Service names:** analyst, config, rag_queen_api

## Examples

```bash
# Rebuild analyst service after code changes
/rebuild analyst

# Rebuild config service
/rebuild config

# Rebuild rag_queen API
/rebuild rag_queen_api
```

## Notes

- Requires Tilt to be running (`tilt up`)
- Tilt UI available at http://localhost:10350
- Service will be rebuilt and restarted automatically
