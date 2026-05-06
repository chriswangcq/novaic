# PR-233A — Queue Active Inbox Dispatch Decision

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Owner | Codex |
| Created | 2026-05-05 |
| Repos | `novaic-agent-runtime`, docs |
| Depends on | PR-233 |

## Objective

Change Queue dispatch semantics so a new IM for a healthy active session is
routed as an active wake inbox attachment, not as a deferred wake-creation
pending trigger.

## Current-State Analysis

`queue_service/session_repo.py::SessionRepository.dispatch()` currently treats
"active session exists" as "buffer trigger into `tq_pending_triggers`". This is
correct for some non-IM retry/recovery cases, but wrong for ordinary user IM
delivery because the running wake does not observe `tq_pending_triggers` until
the active session ends.

## Implementation Scope

- Introduce a small explicit dispatch decision model with typed inputs:
  - active session snapshot
  - trigger type
  - message/notification ids
  - dead/healthy session status if available
- Route active user IM notifications to an explicit active-inbox path.
- Keep wake creation for sleeping/no-active-session cases.
- Keep `tq_pending_triggers` only for recovery or non-attachable triggers.
- Preserve idempotency for repeated dispatches of the same notification.

## Expected Result

Queue dispatch returns a distinct action such as `attached_to_active` for active
IM delivery and publishes a runtime task that appends the input to the current
wake.

## Implementation Result

- Added explicit dispatch decision types in
  `queue_service/session_decisions.py`.
- `SessionRepository.dispatch()` now distinguishes:
  - no active session -> `saga_started`
  - active + attachable message ids -> `attached_to_active`
  - active + non-attachable trigger -> `buffered`
- Attach tasks are published after the DB transaction to avoid reentrant global
  lock acquisition.
- Race losers attach user IMs to the winning wake instead of creating pending
  triggers.

## Verification

- Unit tests:
  - active session + message ids -> active inbox attachment
  - no active session + message ids -> new wake saga
  - active session + no attachable message ids -> existing pending/recovery path
  - duplicate active message dispatch is idempotent
- Review `tq_pending_triggers` call sites and update misleading comments/tests.

## Verification Result

- `tests/test_pr153_pending_inbox_metadata.py`
- `tests/test_pr233_active_inbox_dispatch.py`
