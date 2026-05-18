# Session outbox ownership final verification

## Problem

Rerun focused guards and behavior tests after inventory/classification/fixes to prove session side-effect ownership is durable-outbox based and no dangerous bypass remains.

## Success Criteria

- Rerun focused tests for wake creation outbox, attach outbox, recovery outbox, session-ended/finalize, and observed wake-created state updates.
- Rerun source guards for direct side-effect bypasses.
- Produce final ownership matrix and state whether any dangerous bypass remains.
