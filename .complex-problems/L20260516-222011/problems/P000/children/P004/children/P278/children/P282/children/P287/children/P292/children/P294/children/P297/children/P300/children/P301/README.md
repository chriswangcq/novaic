# Dispatch helper source-shape verification

## Problem

Verify that the start-wake helper refactor physically removed duplicate wake-plan construction and preserved the intended helper boundary in `queue_service/session_repo.py`.

## Success Criteria

- `build_dispatch_wake_plan(` appears exactly once in `session_repo.py`.
- `_queue_start_wake_transition(...)` exists.
- The helper exposes explicit transaction mode via `record_in_current_transaction`.
- Ordinary dispatch and recovery dispatch no longer contain duplicated inline wake-plan construction blocks.
