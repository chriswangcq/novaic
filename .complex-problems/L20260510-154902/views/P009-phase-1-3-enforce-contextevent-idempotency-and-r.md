# P009: Phase 1.3: Enforce ContextEvent idempotency and reset semantics

Status: done
Parent: P002
Root: P000
Package: problems/P000/children/P002/children/P009
Body: problems/P000/children/P002/children/P009/README.md
Ticket(s): T008

## Problem
Implement retry-safe idempotency and no-compat reset semantics for the ContextEvent substrate. This belongs under Phase 1 because retries and old-data reset are core source-of-truth behavior, not later endpoint decoration.

## Success Criteria
- Re-appending with the same idempotency key and same canonical semantic body returns the existing event without appending a duplicate.
- Re-appending with the same idempotency key and a different canonical semantic body raises a clear conflict error.
- Append without idempotency key remains allowed only where the caller explicitly chooses non-idempotent event creation.
- Fresh root initialization records `RootInitialized` without reading/migrating legacy DFS history.
- Unit tests cover idempotent duplicate, idempotency conflict, non-idempotent append behavior, and no-compat initialization.

## Subproblems
- none

## Results
- R006

## Latest Check
C007

## Bodies
- Problem: problems/P000/children/P002/children/P009/README.md
- Ticket T008: problems/P000/children/P002/children/P009/tickets/T008.md
- Result R006: problems/P000/children/P002/children/P009/results/R006.md
- Check C007: problems/P000/children/P002/children/P009/checks/C007.md

## Follow-ups
- none
