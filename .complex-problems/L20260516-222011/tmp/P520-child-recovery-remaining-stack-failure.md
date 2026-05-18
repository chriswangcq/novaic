# Repair Recovery Remaining Stack Failure

## Problem

`test_wake_finalize_failure_records_suspected_dead_event` expects recovery archive `remaining_stack.known == True`, but current behavior reports `False`.

## Success Criteria

- Determine whether unknown remaining stack is intended for failed wake-finalize recovery.
- Apply minimal correct code/test update.
- Rerun the failing test successfully.
