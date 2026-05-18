# P509: Finalize and recovery ownership final verification

Status: done
Parent: P280
Root: P000
Source Ticket: T502 (split)
Source Check: none
Package: problems/P000/children/P004/children/P280/children/P509
Body: problems/P000/children/P004/children/P280/children/P509/README.md
Ticket(s): T505

## Problem
After mapping and any remediation, P280 needs focused tests and final guard evidence proving finalize/watchdog/recovery ownership is coherent and event/FSM/outbox-oriented.

## Success Criteria
- Focused finalize, suspected-dead, recovery, saga compensation, and session-ended tests pass.
- Final guard artifacts show no unclassified ownership bypass.
- The result maps P280 success criteria to saved evidence.
- Any remaining ambiguity is turned into a follow-up problem instead of waived.

## Subproblems
- none

## Results
- R502

## Latest Check
C531

## Bodies
- Problem: problems/P000/children/P004/children/P280/children/P509/README.md
- Ticket T505: problems/P000/children/P004/children/P280/children/P509/tickets/T505.md
- Result R502: problems/P000/children/P004/children/P280/children/P509/results/R502.md
- Check C531: problems/P000/children/P004/children/P280/children/P509/checks/C531.md

## Follow-ups
- none
