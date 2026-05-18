# P331: Attach session outbox delivery audit

Status: done
Parent: P327
Root: P000
Source Ticket: T319 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P331
Body: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P331/README.md
Ticket(s): T321

## Problem
Audit `SessionOutboxDispatcher` attach delivery to verify it requires `expected_session_generation`, preserves it into downstream task/runtime payload, and fails closed on missing generation.

## Success Criteria
- Map attach outbox payload parsing and task/runtime payload creation with file references.
- Verify missing `expected_session_generation` is rejected before delivery.
- Verify delivered payload contains both expected scope and expected generation.
- Identify tests/guards for session outbox attach payload shape.

## Subproblems
- none

## Results
- R316

## Latest Check
C337

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P331/README.md
- Ticket T321: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P331/tickets/T321.md
- Result R316: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P331/results/R316.md
- Check C337: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P331/checks/C337.md

## Follow-ups
- none
