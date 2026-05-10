# P003: Migrate Cortex to common sandbox infrastructure

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Cortex should consume the common primitives and keep only Cortex-specific LogicalFS/Workspace/shell capability semantics.

## Success Criteria
- `novaic-cortex` imports process/mount/filesystem primitives from `common.sandbox`.
- Duplicate generic implementations are removed from Cortex.
- Cortex full tests pass.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
