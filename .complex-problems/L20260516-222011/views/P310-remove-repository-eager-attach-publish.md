# P310: Remove repository eager attach publish

Status: done
Parent: P296
Root: P000
Source Ticket: none (none)
Source Check: C309
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/README.md
Ticket(s): T299

## Problem
`SessionRepository._publish_attach_request_after_transaction(...)` records a durable attach outbox row and then eagerly calls `SessionOutboxDispatcher.publish_attach_input_effect(...)`. This leaves delivery owned by both the repository path and session-outbox-worker.

## Success Criteria
- SessionRepository no longer calls `publish_attach_input_effect` or otherwise publishes attach tasks directly.
- Dispatch attach result returns `delivery=outbox_pending`, `outbox_id`, and no synchronous `task_id` requirement.
- SessionOutboxDispatcher no longer exposes attach-only eager publish API unless another production caller needs it.
- Tests are updated so attach delivery is performed by draining session outbox explicitly.

## Subproblems
- P311: Attach outbox worker-only design
- P312: Attach outbox worker-only implementation
- P313: Attach outbox worker-only verification

## Results
- R300

## Latest Check
C318

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/README.md
- Ticket T299: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/tickets/T299.md
- Result R300: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/results/R300.md
- Check C318: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/checks/C318.md

## Follow-ups
- none
