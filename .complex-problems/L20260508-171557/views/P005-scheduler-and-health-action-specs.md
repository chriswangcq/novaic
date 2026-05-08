# P005: Scheduler And Health Action Specs

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P005
Body: problems/P000/children/P005/README.md
Ticket(s): T005

## Problem
Scheduler and health workers still contain bespoke action orchestration and direct effect execution. Convert them to explicit action specs/plans with centralized effect execution.

## Success Criteria
- Scheduler wake scan/dispatch classification is represented by explicit plan/result classification helpers.
- Health recovery action is represented by explicit plan/spec helpers.
- Engines use the generic plan/effect substrate and no longer call direct effect helpers.
- Tests cover scheduler result classifications and health recovery effects.

## Subproblems
- none

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P005/README.md
- Ticket T005: problems/P000/children/P005/tickets/T005.md
- Result R004: problems/P000/children/P005/results/R004.md
- Check C004: problems/P000/children/P005/checks/C004.md

## Follow-ups
- none
