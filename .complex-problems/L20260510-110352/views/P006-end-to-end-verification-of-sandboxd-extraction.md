# P006: End-to-end verification of sandboxd extraction

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P006
Body: problems/P000/children/P006/README.md
Ticket(s): T006

## Problem
The extraction is only complete if unit, integration, and active-path smoke checks prove sandboxd is actually used and the old path is not silently serving requests.

## Success Criteria
- `novaic-common`, `novaic-sandbox-service`, and `novaic-cortex` tests pass for the changed surfaces.
- A smoke check demonstrates Cortex shell execution routes through sandboxd.
- Service health checks cover sandboxd.
- The final ledger check records remaining risk explicitly; if any active-path gap remains, a follow-up problem is created.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P006/README.md
- Ticket T006: problems/P000/children/P006/tickets/T006.md
- Result R005: problems/P000/children/P006/results/R005.md
- Check C005: problems/P000/children/P006/checks/C005.md

## Follow-ups
- none
