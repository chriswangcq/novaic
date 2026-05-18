# Session-ended handler client route contract

## Problem

The `session.ended` handler, queue client, and queue-service route must enforce and preserve the explicit finalize identity contract instead of depending on repository validation as the first guard.

## Success Criteria

- `task_queue/handlers/session_handlers.py` rejects missing or non-positive `generation` before calling `TaskQueueClient.session_ended(...)`.
- `TaskQueueClient.session_ended(...)` forwards `agent_id`, `subagent_id`, `scope_id`, positive `generation`, `finalize_reason`, and `remaining_stack` unchanged.
- `queue_service/routes.py::SessionEndedRequest` rejects missing/non-positive generation at the API boundary.
- Add tests proving malformed payloads are rejected before delivery and valid payloads are preserved.
