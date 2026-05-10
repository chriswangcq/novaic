# P010: Phase 2A Scope Transition Callsite And Semantics Audit

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P010
Body: problems/P000/children/P003/children/P010/README.md
Ticket(s): T007

## Problem
Before changing hot lifecycle code, identify every scope transition writer/reader, the record shape expected by tests/API, and how it maps to `OperationalSqliteStore.scope_events`. This prevents changing the wrong layer or losing query semantics.

## Success Criteria
- List transition writers and readers with file/function pointers.
- Define the SQLite event payload shape for scope transitions.
- Identify which existing tests need updates.
- State whether NDJSON can be removed in Phase 2 or must be retained temporarily as projection/debug.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P003/children/P010/README.md
- Ticket T007: problems/P000/children/P003/children/P010/tickets/T007.md
- Result R005: problems/P000/children/P003/children/P010/results/R005.md
- Check C005: problems/P000/children/P003/children/P010/checks/C005.md

## Follow-ups
- none
