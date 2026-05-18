# P392: Audit and generic FSM generation classification

Status: done
Parent: P389
Root: P000
Source Ticket: T380 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/README.md
Ticket(s): T385

## Problem
Widened guard hits remain in audit/projector code and generic task/saga/lease FSM infrastructure. These may be safe counters/adapters, but they need explicit classification so session-generation cleanup does not leave misleading residue.

## Success Criteria
- Classify `session_audit.py`, `queue_audit.py`, `task_fsm.py`, `saga_fsm.py`, `lease_fsm.py`, `queue_db.py`, and `saga_repo.py` generation hits.
- Patch any live authority path that silently defaults generation in a way that can accept stale input.
- Leave only documented safe counter/projection hits.
- Run focused tests for any changed modules.

## Subproblems
- P396: Audit and projection generation classification
- P397: Generic FSM generation counter classification

## Results
- R379

## Latest Check
C402

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/README.md
- Ticket T385: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/tickets/T385.md
- Result R379: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/results/R379.md
- Check C402: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/checks/C402.md

## Follow-ups
- none
