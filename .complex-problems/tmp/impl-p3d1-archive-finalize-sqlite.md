# Archive Finalize Stack Snapshot Cutover

## Problem

`scope_end` still uses `_collect_active_stack(...)` to build remaining-stack data before writing `wake_archived` / final active-stack projection events. This keeps file-walk stack snapshots on an archive/finalize authority path after SQLite projection became the runtime stack source.

This belongs under Phase 3D because archive/finalize is a separate lifecycle path from live begin/end, and it can be verified independently with root, wake, and child archive scenarios.

## Success Criteria

- `scope_end` root and child archive paths derive active stack frames from `read_active_stack_projection(...)`, not `_collect_active_stack(...)`.
- `_append_wake_archived_event(...)` and `_finalize_active_stack_for_archive(...)` receive projection-derived frames.
- Idempotent already-archived archive paths keep existing API behavior.
- Tests cover root archive, wake child archive with remaining stack, and archive retry/idempotency behavior.
