# P521: Repair Recovery Remaining Stack Failure

Status: done
Parent: P520
Root: P000
Source Ticket: T514 (split)
Source Check: none
Package: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P521
Body: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P521/README.md
Ticket(s): T515

## Problem
`test_wake_finalize_failure_records_suspected_dead_event` expects recovery archive `remaining_stack.known == True`, but current behavior reports `False`.

## Success Criteria
- Determine whether unknown remaining stack is intended for failed wake-finalize recovery.
- Apply minimal correct code/test update.
- Rerun the failing test successfully.

## Subproblems
- none

## Results
- R510

## Latest Check
C541

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P521/README.md
- Ticket T515: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P521/tickets/T515.md
- Result R510: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P521/results/R510.md
- Check C541: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P521/checks/C541.md

## Follow-ups
- none
