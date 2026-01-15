---
name: test-service
description: Run comprehensive tests for a service (analyst, config, rag_queen, common)
allowed-tools:
  - Bash
  - Read
---

# Test Service

Run comprehensive tests for a backend service with options for unit tests, integration tests, and coverage reporting.

## Usage

```
/test-service <service-name> [options]
```

**Service names:** analyst, config, rag_queen, common

**Options:**
- `--integration` - Run integration tests (default: unit tests only)
- `--all` - Run both unit and integration tests
- `--cov` - Generate coverage report
- `-v` - Verbose output
- `-k "test_name"` - Run specific test by name

## Examples

```bash
# Run unit tests for analyst service
/test-service analyst

# Run all tests with coverage
/test-service analyst --all --cov

# Run specific test
/test-service config -k "test_data_source"

# Run integration tests only
/test-service rag_queen --integration
```

## Notes

- Default runs unit tests only for fast feedback
- Unit tests run in existing Tilt dev containers if available (~2 seconds)
- Falls back to dedicated test container if Tilt not running (~30 seconds)
- Integration tests always use dedicated containers with isolated databases
- Start Tilt (`tilt up`) before running tests for fastest execution
