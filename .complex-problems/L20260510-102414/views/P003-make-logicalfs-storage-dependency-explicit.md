# P003: Make LogicalFS storage dependency explicit

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
LogicalFS currently reaches into `Workspace._store` and `_key`, which works but hides the intended boundary: LogicalFS should depend on a workspace/storage port, while Blob/store remains the lower byte-object substrate.

## Success Criteria
- LogicalFS uses a public workspace-facing method or small explicit port for listing materialized paths.
- Private workspace internals are not the normal LogicalFS dependency.
- Tests still prove `/ro` materialization and `/rw` flush semantics.

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
