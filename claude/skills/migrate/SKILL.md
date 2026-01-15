---
name: migrate
description: Create and apply database migrations for a service
allowed-tools:
  - Bash
---

# Database Migration Helper

Create new database migrations or apply existing migrations for a service.

## Usage

### Create a new migration
```
/migrate create <service> <description>
```

### Apply migrations
```
/migrate apply <service>
```

**Service names:** analyst, config, artifact, rag_queen

## Examples

```bash
# Create a new migration for the analyst service
/migrate create analyst "add user preferences table"

# Apply pending migrations to config service
/migrate apply config

# Create migration for config service
/migrate create config "add data source encryption fields"
```

## Notes

- Each service has its own database and migration history
- Migrations are created in `services/<service>/migrations/versions/`
- Always review generated migrations before applying
- Use descriptive migration messages
