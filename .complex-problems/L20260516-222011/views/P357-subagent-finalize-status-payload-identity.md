# P357: Subagent finalize status payload identity

Status: done
Parent: P354
Root: P000
Source Ticket: T341 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P357
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P357/README.md
Ticket(s): T342

## Problem
`wake_finalize` currently builds `set_subagent_sleeping` and `set_subagent_completed` payloads from coarse `agent_id/subagent_id` only. Terminal Business status updates need explicit wake/session identity in their payloads so downstream handlers can reject malformed finalize tasks and tests can prove no legacy `last_scope_id` field is used.

## Success Criteria
- Inspect `task_queue/sagas/wake_finalize.py` status payload builders.
- Add explicit current finalize identity to both terminal-status payloads, including `scope_id` and positive `session_generation`.
- Preserve existing `agent_id/subagent_id` fields and `result` semantics for completed payloads.
- Do not add or reintroduce `last_scope_id`.
- Add focused tests proving both payload builders carry the new identity and reject missing/non-positive generation.

## Subproblems
- none

## Results
- R334

## Latest Check
C355

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P357/README.md
- Ticket T342: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P357/tickets/T342.md
- Result R334: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P357/results/R334.md
- Check C355: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P357/checks/C355.md

## Follow-ups
- none
