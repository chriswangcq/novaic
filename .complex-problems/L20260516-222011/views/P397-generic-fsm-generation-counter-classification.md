# P397: Generic FSM generation counter classification

Status: done
Parent: P392
Root: P000
Source Ticket: T385 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P397
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P397/README.md
Ticket(s): T387

## Problem
`task_fsm.py`, `saga_fsm.py`, `lease_fsm.py`, `queue_db.py`, and `saga_repo.py` contain generation counters for non-session FSMs. They must be classified separately from session generation authority.

## Success Criteria
- Generic FSM generation hits are classified as internal state-version counters or patched if externally malformed input can affect authority.
- Existing task/saga/lease focused tests pass.
- Final matrix avoids confusing generic FSM generation with Queue session generation.

## Subproblems
- none

## Results
- R378

## Latest Check
C401

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P397/README.md
- Ticket T387: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P397/tickets/T387.md
- Result R378: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P397/results/R378.md
- Check C401: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P397/checks/C401.md

## Follow-ups
- none
