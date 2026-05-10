# P046: Remove runtime lifecycle methods

Status: done
Parent: P043
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043/children/P046
Body: problems/P000/children/P004/children/P028/children/P043/children/P046/README.md
Ticket(s): T042

## Problem
`novaic_cortex.runtime.Cortex` still defines `scope_create` and `scope_end`, so runtime callers can create or archive scope files directly through Workspace without emitting ContextEvents. This is a bypass even if active production code no longer uses it.

## Success Criteria
- `Cortex.scope_create` and `Cortex.scope_end` are physically removed from `novaic_cortex/runtime.py`.
- Runtime façade documentation/comments no longer advertise internal scope lifecycle management.
- A guard test asserts the runtime façade does not expose these methods.
- Focused runtime import/guard tests pass.

## Subproblems
- none

## Results
- R038

## Latest Check
C041

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/children/P046/README.md
- Ticket T042: problems/P000/children/P004/children/P028/children/P043/children/P046/tickets/T042.md
- Result R038: problems/P000/children/P004/children/P028/children/P043/children/P046/results/R038.md
- Check C041: problems/P000/children/P004/children/P028/children/P043/children/P046/checks/C041.md

## Follow-ups
- none
