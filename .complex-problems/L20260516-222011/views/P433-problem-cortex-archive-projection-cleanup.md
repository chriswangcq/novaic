# P433: Problem: Cortex archive projection cleanup

Status: done
Parent: P418
Root: P000
Source Ticket: T418 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/children/P433
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/children/P433/README.md
Ticket(s): T421

## Problem
Archive projection/readback paths may still walk old files or expose stale/debug-oriented shapes that should not be part of the live ContextEvent contract.

## Success Criteria
- Archive projection paths are classified.
- Live stale/debug-only projection residue is removed or isolated.
- Tests or guards prove archive projections do not reintroduce raw payload/context leakage.

## Subproblems
- none

## Results
- R414

## Latest Check
C440

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/children/P433/README.md
- Ticket T421: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/children/P433/tickets/T421.md
- Result R414: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/children/P433/results/R414.md
- Check C440: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/children/P433/checks/C440.md

## Follow-ups
- none
