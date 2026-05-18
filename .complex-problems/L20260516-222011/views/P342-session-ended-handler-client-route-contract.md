# P342: Session-ended handler client route contract

Status: done
Parent: P336
Root: P000
Source Ticket: T327 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P342
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P342/README.md
Ticket(s): T330

## Problem
The `session.ended` handler, queue client, and queue-service route must enforce and preserve the explicit finalize identity contract instead of depending on repository validation as the first guard.

## Success Criteria
- `task_queue/handlers/session_handlers.py` rejects missing or non-positive `generation` before calling `TaskQueueClient.session_ended(...)`.
- `TaskQueueClient.session_ended(...)` forwards `agent_id`, `subagent_id`, `scope_id`, positive `generation`, `finalize_reason`, and `remaining_stack` unchanged.
- `queue_service/routes.py::SessionEndedRequest` rejects missing/non-positive generation at the API boundary.
- Add tests proving malformed payloads are rejected before delivery and valid payloads are preserved.

## Subproblems
- none

## Results
- R324

## Latest Check
C345

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P342/README.md
- Ticket T330: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P342/tickets/T330.md
- Result R324: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P342/results/R324.md
- Check C345: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P342/checks/C345.md

## Follow-ups
- none
