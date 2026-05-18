# P358: Subagent finalize status handler validation

Status: done
Parent: P354
Root: P000
Source Ticket: T341 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P358
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P358/README.md
Ticket(s): T343

## Problem
`handle_subagent_set_sleeping()` and `handle_subagent_set_completed()` can currently call `business_client.entity_update()` without validating wake/session identity. Missing or non-positive generation must be rejected before any Business mutation.

## Success Criteria
- Inspect `task_queue/handlers/subagent_handlers.py` terminal status handlers.
- Require `scope_id` and positive `session_generation` before `entity_update()`.
- Keep Business update schema minimal; do not write unknown audit fields unless code-backed evidence shows they are accepted.
- Add tests that missing `scope_id`, missing generation, zero generation, and malformed generation fail before Business mutation.
- Keep non-finalize subagent handlers unchanged unless a direct dependency is proven.

## Subproblems
- none

## Results
- R335

## Latest Check
C356

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P358/README.md
- Ticket T343: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P358/tickets/T343.md
- Result R335: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P358/results/R335.md
- Check C356: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P358/checks/C356.md

## Follow-ups
- none
