# P008: Add stable running reasoning activity projection updates

Status: done
Parent: P002
Root: P000
Source Ticket: T004 (split)
Source Check: none
Package: problems/P000/children/P002/children/P008
Body: problems/P000/children/P002/children/P008/README.md
Ticket(s): T006

## Problem
Runtime needs a projection helper that can update one stable reasoning row during streaming and finalize it after the complete response arrives, without duplicating rows or writing every token.

## Success Criteria
- Projection helper emits a deterministic record id for the current agent/scope/round reasoning row.
- Running updates set `phase=reasoning`, `public_title=正在思考`, `status=running`, and current text.
- Final update sets completed status and final text/public title.
- Tests cover stable IDs, running/final status, and coalescing throttle behavior.

## Subproblems
- none

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P002/children/P008/README.md
- Ticket T006: problems/P000/children/P002/children/P008/tickets/T006.md
- Result R004: problems/P000/children/P002/children/P008/results/R004.md
- Check C004: problems/P000/children/P002/children/P008/checks/C004.md

## Follow-ups
- none
