# P017: Inspect and clean stale local branches

Status: done
Parent: P006
Root: P000
Source Ticket: T015 (split)
Source Check: none
Package: problems/P000/children/P006/children/P017
Body: problems/P000/children/P006/children/P017/README.md
Ticket(s): T017

## Problem
The local repository has several old branches. Clean stale local branches only after inspecting whether they are merged or contain unique work that should not be deleted.

## Success Criteria
- Current branch remains `main`.
- Local branches are listed and inspected.
- Branches deleted locally are safe stale branches or already merged branches.
- Branches with unique unmerged work are preserved and documented.
- No uncommitted work is reverted.

## Subproblems
- none

## Results
- R015

## Latest Check
C016

## Bodies
- Problem: problems/P000/children/P006/children/P017/README.md
- Ticket T017: problems/P000/children/P006/children/P017/tickets/T017.md
- Result R015: problems/P000/children/P006/children/P017/results/R015.md
- Check C016: problems/P000/children/P006/children/P017/checks/C016.md

## Follow-ups
- none
