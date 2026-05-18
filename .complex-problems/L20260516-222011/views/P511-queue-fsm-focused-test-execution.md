# P511: Queue FSM Focused Test Execution

Status: done
Parent: P281
Root: P000
Source Ticket: T506 (split)
Source Check: none
Package: problems/P000/children/P004/children/P281/children/P511
Body: problems/P000/children/P004/children/P281/children/P511/README.md
Ticket(s): T512

## Problem
Run the focused queue/session/FSM/outbox/finalize tests identified by the inventory.

## Success Criteria
- Focused test command exits successfully, or failures are captured with enough detail for follow-up.
- Exact command, pytest counts, and log path are recorded.
- Test scope covers dispatch, session state, outbox, finalize, recovery, saga compensation, and FSM decisions.

## Subproblems
- P517: Session Outbox Finalize Focused Tests
- P518: Task Saga Worker FSM Focused Tests
- P519: Unit Tool Output and Task Queue Focused Tests

## Results
- R523

## Latest Check
C556

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P511/README.md
- Ticket T512: problems/P000/children/P004/children/P281/children/P511/tickets/T512.md
- Result R523: problems/P000/children/P004/children/P281/children/P511/results/R523.md
- Check C556: problems/P000/children/P004/children/P281/children/P511/checks/C556.md

## Follow-ups
- none
