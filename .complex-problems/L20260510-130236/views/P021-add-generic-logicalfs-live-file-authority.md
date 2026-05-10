# P021: Add Generic LogicalFS Live File Authority

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P019/children/P021
Body: problems/P000/children/P019/children/P021/README.md
Ticket(s): T021

## Problem
LogicalFS currently provides materialization/view primitives, but it does not yet own a generic live file authority for realtime `RO` / `RW` reads and writes. The current authority lives in Cortex and knows Cortex persistence details. This belongs under T019 because the final architecture requires LogicalFS, not Cortex, to be the live file boundary.

## Success Criteria
- `novaic-logicalfs` exposes a business-independent live file authority contract for logical path reads, writes, list, delete, append, and move operations.
- The authority accepts explicit owner/layout inputs instead of reading agent/Cortex state implicitly.
- The authority can be backed by a generic object store adapter without importing `novaic-cortex`.
- Unit tests in `novaic-logicalfs` prove path mapping, directory listing, tree moves, append behavior, and invalid path rejection.
- The implementation is not merely copied under a new name with Cortex semantics still embedded.

## Subproblems
- none

## Results
- R020

## Latest Check
C020

## Bodies
- Problem: problems/P000/children/P019/children/P021/README.md
- Ticket T021: problems/P000/children/P019/children/P021/tickets/T021.md
- Result R020: problems/P000/children/P019/children/P021/results/R020.md
- Check C020: problems/P000/children/P019/children/P021/checks/C020.md

## Follow-ups
- none
