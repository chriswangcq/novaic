# Suppress high-frequency successful polling logs

## Problem

Successful worker claim polling emits INFO lines through dependency HTTP logs and internal access logs. This can grow logs fast enough to fill disk, which then breaks Redis persistence and downstream Cortex writes.

## Success Criteria

- Service logging bootstrap quiets `httpx`, `httpcore`, and `uvicorn.access` to warning level.
- Successful `/api/queue/tasks/claim` and `/api/queue/sagas/claim` internal access logs are suppressed.
- Failed claim requests still log.
- Tests cover the hot-path suppression logic.
