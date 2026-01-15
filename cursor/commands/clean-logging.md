# Clean Up Logging

## Overview
Go through the listed files and clean up the logging so that the app is production ready. This mainly involves changing non-essential logs to debug level instead of info level.

## The Process
- Go through each file listed and ready. This mainly involves changing non-essential logs to debug level instead of info level.
- Then find all the log statements, then determine if that log statement is useful in production.
  - Does it tell us specifically that some high level process has started or completed?
  - Then if the answer is yes leave it at info level if the answer is no change it to debug level.
  - Also look for error and warning messages as a general rule only errors that are not recoverable should be logged as errors (i.e., things that we need to make an intervention on - human intervention).
  - If it's just catching an exception and then moving on (e.g., an endpoint returned 404 or a tool call failed but we can keep going), then it should just be warning level.
  - Errors should always be logged with exc_info=True so we get the full stack trace.

## Examples:

Keep as is:
```python
logger.info("Starting integration source introspection for: %s", integration_source_id)
logger.info("Completed integration source introspection for: %s", integration_source_id)
logger.info("Error occurred while introspecting integration source: %s", integration_source_id)
```

Change these to debug:
```python
logger.info("Successfully retrieved %s fields from record structure", len(fields))
logger.info("Top-level object fields: %s", [f.api_identifier for f in fields if '.' not in f.api_identifier])
logger.info("Sample nested fields: %s", [f.api_identifier for f in fields if '.' in f.api_identifier][:20])
logger.info("requested fields: %s", [f.api_identifier for f in fields])
```
should be changed to:
```python
logger.debug("Successfully retrieved %s fields from record structure", len(fields))
logger.debug("Top-level object fields: %s", [f.api_identifier for f in fields if '.' not in f.api_identifier])
logger.debug("Sample nested fields: %s", [f.api_identifier for f in fields if '.' in f.api_identifier][:20])
logger.debug("requested fields: %s", [f.api_identifier for f in fields])
```

Keep as is:
```python
logger.error("Unable to introspect integration source %s: %s", integration_source_id, e, exc_info=True)
```

Change these to warning:
```python
logger.error("SaaS object %s was deleted, skipping embedding", object_id, exc_info=True)
logger.error("SaaS object %s was deleted, skipping description generation", object_id, exc_info=True)
logger.error("Failed to delete stale field %s: %s", existing_field.get('field_name'), delete_error, exc_info=True)
logger.error("Tool call failed: %s", tool_call_id, exc_info=True)
```
should be changed to:
```python
logger.warning("SaaS object %s was deleted, skipping embedding", object_id)
logger.warning("SaaS object %s was deleted, skipping description generation", object_id)
logger.warning("Failed to delete stale field %s: %s", existing_field.get('field_name'), delete_error)
logger.warning("Tool call failed: %s", tool_call_id)
```
