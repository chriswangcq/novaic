# P022: Remove tracked generated complex-problems dashboard residue

Status: done
Parent: P019
Root: P000
Source Ticket: none (none)
Source Check: C010
Package: problems/P000/children/P001/children/P009/children/P015/children/P019/children/P022
Body: problems/P000/children/P001/children/P009/children/P015/children/P019/children/P022/README.md
Ticket(s): T013

## Problem
The tracked `dashboards/complex-problems-dashboard.html` generated snapshot is stale, large, and pollutes architecture residue scans. Remove it from source and prevent future generated dashboard HTML from being committed accidentally.

## Success Criteria
- `dashboards/complex-problems-dashboard.html` is deleted from the tracked source tree.
- The repository ignores generated dashboard HTML if appropriate.
- Residue searches no longer return this stale dashboard as a hit.
- The deletion does not remove the real `.complex-problems` ledger source of truth.

## Subproblems
- none

## Results
- R009

## Latest Check
C011

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P019/children/P022/README.md
- Ticket T013: problems/P000/children/P001/children/P009/children/P015/children/P019/children/P022/tickets/T013.md
- Result R009: problems/P000/children/P001/children/P009/children/P015/children/P019/children/P022/results/R009.md
- Check C011: problems/P000/children/P001/children/P009/children/P015/children/P019/children/P022/checks/C011.md

## Follow-ups
- none
