# P315: Remove stale attach task_id assumption

Status: done
Parent: P314
Root: P000
Source Ticket: T302 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P315
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P315/README.md
Ticket(s): T303

## Problem
`SessionRepository.dispatch()` still logs `result["task_id"]` after attach dispatch. The attach worker-only cutover intentionally returns an outbox-pending result with `outbox_id`, so this stale assumption crashes dispatch before the result can be returned.

## Success Criteria
- Attach dispatch logging no longer reads `result["task_id"]`.
- The log line reports durable worker-owned delivery information such as `outbox_id` and `delivery`.
- The active attach result still returns `delivery=outbox_pending`, `outbox_id`, `saga_id`, and `scope_id`.
- No eager attach publish path is reintroduced.

## Subproblems
- none

## Results
- R295

## Latest Check
C312

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P315/README.md
- Ticket T303: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P315/tickets/T303.md
- Result R295: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P315/results/R295.md
- Check C312: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P315/checks/C312.md

## Follow-ups
- none
