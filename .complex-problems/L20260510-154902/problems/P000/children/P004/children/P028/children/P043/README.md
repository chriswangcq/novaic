# Phase 3.6.2: Remove runtime direct structural scope lifecycle bypass

## Problem

`Cortex.scope_create/end` still directly call Workspace lifecycle writes and are used by legacy tests. They are not the active queue-service path, but they remain a direct code path that can create/archive scope state without the event-wired API helpers.

## Success Criteria

- `Cortex.scope_create/end` direct lifecycle helpers are removed or made unreachable from runtime writes.
- Tests using those helpers are deleted, rewritten to API/context paths, or converted to guard tests.
- No runtime direct structural lifecycle helper can bypass ContextEvent writers.
- Full Cortex suite passes.
