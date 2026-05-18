# P486: Session outbox dispatcher boundary hardening

Status: done
Parent: P481
Root: P000
Source Ticket: T476 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P481/children/P486
Body: problems/P000/children/P004/children/P279/children/P481/children/P486/README.md
Ticket(s): T479

## Problem
`session_outbox.py` is intentionally the production boundary where durable session outbox effects become saga creation or queue publishes. Because it is a sanctioned direct side-effect location, it needs narrow guards proving that session-owned side effects do not appear elsewhere.

## Success Criteria
- Session outbox dispatcher direct effects are documented as the required boundary.
- Guards/tests verify `.saga_orchestrator.create(` and session-owned `queue.publish` effects remain limited to the intended dispatcher or explicit worker boundaries.
- Any discovered session-owned side-effect bypass outside the dispatcher is removed or split.
- Focused session outbox tests pass.

## Subproblems
- none

## Results
- R475

## Latest Check
C504

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P481/children/P486/README.md
- Ticket T479: problems/P000/children/P004/children/P279/children/P481/children/P486/tickets/T479.md
- Result R475: problems/P000/children/P004/children/P279/children/P481/children/P486/results/R475.md
- Check C504: problems/P000/children/P004/children/P279/children/P481/children/P486/checks/C504.md

## Follow-ups
- none
