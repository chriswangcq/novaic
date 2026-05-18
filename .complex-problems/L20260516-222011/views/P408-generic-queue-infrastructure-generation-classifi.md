# P408: Generic Queue infrastructure generation classification

Status: done
Parent: P403
Root: P000
Source Ticket: T395 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P408
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P408/README.md
Ticket(s): T397

## Problem
Generic Queue infrastructure files (`queue_db`, `saga_repo`, `task_fsm`, generic FSM state stores) contain `generation` and `or 0` patterns. These may be valid infrastructure counters, but they must be explicitly classified or patched if they influence live session authority.

## Success Criteria
- Inspect `queue_db.py`, `saga_repo.py`, `task_fsm.py`, and generic FSM generation hits from P402.
- Distinguish generic FSM generations from live session-generation authority.
- Patch dangerous live session-adjacent defaults, or document safe generic semantics with tests/evidence.
- Add focused tests if any generic infrastructure boundary is changed.
- Rerun generic Queue infrastructure guards.

## Subproblems
- none

## Results
- R391

## Latest Check
C417

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P408/README.md
- Ticket T397: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P408/tickets/T397.md
- Result R391: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P408/results/R391.md
- Check C417: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P408/checks/C417.md

## Follow-ups
- none
