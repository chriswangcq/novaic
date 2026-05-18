# P485: Generic task publish route boundary decision

Status: done
Parent: P481
Root: P000
Source Ticket: T476 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P481/children/P485
Body: problems/P000/children/P004/children/P279/children/P481/children/P485/README.md
Ticket(s): T478

## Problem
`queue_service/routes.py` exposes a generic `/tasks/publish` path that directly calls `queue.publish`. It may be a legitimate internal adapter boundary, but it is the most visible direct publish API and should be explicitly decided rather than hand-waved.

## Success Criteria
- The `/tasks/publish` route and any related direct route publish behavior are inspected.
- The decision is recorded: retain as adapter boundary, tighten with explicit contract/guard, or remove/replace.
- If retained, tests or guard evidence prove it does not bypass session-owned FSM/outbox rules.
- If changed, focused route/queue tests pass.

## Subproblems
- none

## Results
- R474

## Latest Check
C503

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P481/children/P485/README.md
- Ticket T478: problems/P000/children/P004/children/P279/children/P481/children/P485/tickets/T478.md
- Result R474: problems/P000/children/P004/children/P279/children/P481/children/P485/results/R474.md
- Check C503: problems/P000/children/P004/children/P279/children/P481/children/P485/checks/C503.md

## Follow-ups
- none
