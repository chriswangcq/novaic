# P043: Phase 3.6.2: Remove runtime direct structural scope lifecycle bypass

Status: done
Parent: P028
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043
Body: problems/P000/children/P004/children/P028/children/P043/README.md
Ticket(s): T041

## Problem
`Cortex.scope_create/end` still directly call Workspace lifecycle writes and are used by legacy tests. They are not the active queue-service path, but they remain a direct code path that can create/archive scope state without the event-wired API helpers.

## Success Criteria
- `Cortex.scope_create/end` direct lifecycle helpers are removed or made unreachable from runtime writes.
- Tests using those helpers are deleted, rewritten to API/context paths, or converted to guard tests.
- No runtime direct structural lifecycle helper can bypass ContextEvent writers.
- Full Cortex suite passes.

## Subproblems
- P046: Remove runtime lifecycle methods
- P047: Migrate runtime lifecycle helper tests
- P048: Verify runtime lifecycle bypass removal

## Results
- R046

## Latest Check
C049

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/README.md
- Ticket T041: problems/P000/children/P004/children/P028/children/P043/tickets/T041.md
- Result R046: problems/P000/children/P004/children/P028/children/P043/results/R046.md
- Check C049: problems/P000/children/P004/children/P028/children/P043/checks/C049.md

## Follow-ups
- none
