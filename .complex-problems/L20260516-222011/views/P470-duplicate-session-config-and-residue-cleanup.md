# P470: Duplicate session config and residue cleanup

Status: done
Parent: P466
Root: P000
Source Ticket: T460 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/README.md
Ticket(s): T470

## Problem
Clean up duplicate configuration/residue discovered during hidden-input review, including repeated literals or duplicate branch logic that can confuse future maintenance. This includes the currently observed duplicated `remaining_stack` error string if still present.

## Success Criteria
- Remove exact duplicate literals/branches in session/worker config paths where they add no semantic value.
- Keep process-boundary configuration explicit and centralized.
- Add or update focused tests/guards if the cleanup affects behavior.
- Prove no compatibility branch or stale duplicate remains in the touched area.

## Subproblems
- P479: Rerun duplicate residue guard from repo root

## Results
- R465

## Latest Check
C495

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/README.md
- Ticket T470: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/tickets/T470.md
- Result R465: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/results/R465.md
- Check C493: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/checks/C493.md
- Check C495: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/checks/C495.md

## Follow-ups
- P479: Rerun duplicate residue guard from repo root
