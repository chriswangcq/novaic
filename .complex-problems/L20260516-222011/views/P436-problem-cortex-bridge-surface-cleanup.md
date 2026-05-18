# P436: Problem: Cortex bridge surface cleanup

Status: done
Parent: P419
Root: P000
Source Ticket: T422 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/README.md
Ticket(s): T425

## Problem
Runtime bridge clients may still call old Cortex endpoints, full-payload reads, or compatibility paths.

## Success Criteria
- Runtime bridge call sites are inventoried.
- Calls use current explicit endpoints/projection modes.
- Focused runtime bridge tests/guards pass or gaps are split.

## Subproblems
- P437: Runtime bridge endpoint inventory
- P438: Agent loop prepare-path proof
- P439: Context endpoint ownership and migration
- P440: Final runtime bridge guard verification

## Results
- R427

## Latest Check
C453

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/README.md
- Ticket T425: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/tickets/T425.md
- Result R427: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/results/R427.md
- Check C453: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/checks/C453.md

## Follow-ups
- none
