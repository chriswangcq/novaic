# P003: Suppress high-frequency successful polling logs

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Successful worker claim polling emits INFO lines through dependency HTTP logs and internal access logs. This can grow logs fast enough to fill disk, which then breaks Redis persistence and downstream Cortex writes.

## Success Criteria
- Service logging bootstrap quiets `httpx`, `httpcore`, and `uvicorn.access` to warning level.
- Successful `/api/queue/tasks/claim` and `/api/queue/sagas/claim` internal access logs are suppressed.
- Failed claim requests still log.
- Tests cover the hot-path suppression logic.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
