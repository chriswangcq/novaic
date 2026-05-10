# Phase 3C Runtime Stack Read And LIFO Cutover

## Problem

Runtime stack reads and LIFO mismatch checks still rely on file-walk projection. They must use operational SQLite projection as the control-plane authority.

## Success Criteria

- `context_status` reads default stack frames from SQLite active-stack projection.
- `skill_begin` determines parent/top scope from SQLite, not `_collect_active_stack`.
- `skill_end` validates current top scope from SQLite, not `_collect_active_stack`.
- Structured mismatch and empty-stack errors preserve existing API semantics.
- Tests cover wrong-scope close, stack-empty behavior, and open-child behavior after a fresh registry/workspace instance.
