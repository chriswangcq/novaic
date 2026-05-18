# P461: Dispatcher direct call classification

Status: done
Parent: P459
Root: P000
Source Ticket: T452 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P461
Body: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P461/README.md
Ticket(s): T453

## Problem
Classify direct `saga_orchestrator.create(...)` and `queue.publish(...)` calls inside `SessionOutboxDispatcher` and verify whether they are safe implementation details below durable outbox ownership.

## Success Criteria
- Save source guard output for dispatcher direct calls.
- Classify each direct call with file references.
- If any call can be reached without a durable outbox row, create/fix a concrete follow-up.
- Run focused tests if source changes are made.

## Subproblems
- none

## Results
- R448

## Latest Check
C474

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P461/README.md
- Ticket T453: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P461/tickets/T453.md
- Result R448: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P461/results/R448.md
- Check C474: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P461/checks/C474.md

## Follow-ups
- none
