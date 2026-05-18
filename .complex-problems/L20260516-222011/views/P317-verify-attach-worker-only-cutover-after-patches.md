# P317: Verify attach worker-only cutover after patches

Status: done
Parent: P314
Root: P000
Source Ticket: T302 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P317
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P317/README.md
Ticket(s): T305

## Problem
After the logger and boundary test fixes, the attach worker-only cutover needs correct compile and focused test verification from the right working directory, followed by a broader session FSM/outbox focused suite if the first suite passes.

## Success Criteria
- `python3 -m py_compile queue_service/session_repo.py queue_service/session_outbox.py` passes from `novaic-agent-runtime`.
- Focused attach/boundary tests pass from `novaic-agent-runtime`.
- Broader session FSM/outbox focused tests pass from `novaic-agent-runtime` or any failure is recorded as a new explicit follow-up.
- Verification confirms no new eager attach publish path exists.

## Subproblems
- none

## Results
- R297

## Latest Check
C314

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P317/README.md
- Ticket T305: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P317/tickets/T305.md
- Result R297: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P317/results/R297.md
- Check C314: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P317/checks/C314.md

## Follow-ups
- none
