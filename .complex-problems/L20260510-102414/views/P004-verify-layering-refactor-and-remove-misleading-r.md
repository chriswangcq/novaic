# P004: Verify layering refactor and remove misleading residue

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T004

## Problem
After extraction and boundary cleanup, verify that active code still works and that no old fallback/duplicate path remains to mislead future maintenance.

## Success Criteria
- Targeted tests pass or any environment skip is explicitly explained.
- Import/compile checks pass.
- Residue scans show no local fallback, command rewrite fallback, or stale duplicate shell path implementations.
- Ledger check records remaining risk honestly.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T004: problems/P000/children/P004/tickets/T004.md
- Result R003: problems/P000/children/P004/results/R003.md
- Check C003: problems/P000/children/P004/checks/C003.md

## Follow-ups
- none
