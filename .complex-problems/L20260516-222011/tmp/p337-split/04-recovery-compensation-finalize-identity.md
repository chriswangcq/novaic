# Recovery compensation finalize identity

## Problem

Recovery and compensation paths can synthesize wake-finalize contexts after failures. They must preserve or require explicit session generation and wake scope identity rather than creating ambiguous finalize tasks.

## Success Criteria

- Inspect `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, recovery tests, and compensation tests.
- Verify compensation-created `wake_finalize` contexts carry positive session generation when the failed saga had one.
- Ensure missing generation in compensation/recovery is either rejected or explicitly routed to a dead-session/recovery path without mutating a newer active session.
- Add or update tests for compensation/recovery generation preservation.
