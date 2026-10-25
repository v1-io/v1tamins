---
"v1tamins": patch
---

Preserve server-wrapper cancellation status when a macOS process group briefly rejects signals while exiting, as exposed by Python 3.15 event-driven waits. Confirm group disappearance before treating a permission error as completed cleanup; retain real permission failures and force-stop TERM-ignoring descendants.

Continue cleaning up every owned command/server group even when another group has a genuine permission failure, then report the original failure.
