# P442: Materialized context owner classification

Status: done
Parent: P439
Root: P000
Source Ticket: T429 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P442
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P442/README.md
Ticket(s): T430

## Problem
Before renaming or deleting materialized context bridge helpers, classify each live use of `/v1/context/read`, `/v1/context/append`, and `/v1/context/batch` by its actual owner and purpose.

## Success Criteria
- Every live runtime/Cortex/test hit is classified as notification projection, assistant/system timeline projection, API test, debug/API compatibility, or dead residue.
- Evidence artifacts are saved.
- No code is changed in this child.
- The classification explicitly identifies which child should handle each non-clean owner.

## Subproblems
- none

## Results
- R421

## Latest Check
C447

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P442/README.md
- Ticket T430: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P442/tickets/T430.md
- Result R421: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P442/results/R421.md
- Check C447: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P442/checks/C447.md

## Follow-ups
- none
