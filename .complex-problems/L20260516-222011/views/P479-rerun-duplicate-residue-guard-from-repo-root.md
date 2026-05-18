# P479: Rerun duplicate residue guard from repo root

Status: done
Parent: P470
Root: P000
Source Ticket: none (none)
Source Check: C493
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/children/P479
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/children/P479/README.md
Ticket(s): T471

## Problem
The P470 duplicate/residue guard failed to write its artifact because the command ran from `novaic-agent-runtime` with a repo-root-relative output path. Rerun the guard from the repo root and save the required artifact.

## Success Criteria
- Create `.complex-problems/L20260516-222011/tmp/p470/duplicate-residue-guard.txt`.
- Prove the adjacent duplicated `remaining_stack` string pattern is absent.
- Prove focused residue tests already passed or rerun them if needed.

## Subproblems
- none

## Results
- R466

## Latest Check
C494

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/children/P479/README.md
- Ticket T471: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/children/P479/tickets/T471.md
- Result R466: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/children/P479/results/R466.md
- Check C494: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P470/children/P479/checks/C494.md

## Follow-ups
- none
