# PR-168 — Environment Notification Queue Cutover

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-business`, `novaic-agent-runtime`, `novaic-common`, docs |
| Depends on | PR-167 |
| Theme | Agent loop ownership |

## Goal

Move wake triggering, claiming, processing, and failure semantics from message lifecycle wrappers to dedicated Environment notifications.

## Current-State Analysis

The current notification-only prompt works, but `notification_id` is still the message id and lifecycle uses `chat_messages.lifecycle`. Runtime resolves current wake ids from Cortex meta and calls `im_read`, while Business maps message lifecycle into Environment states.

## Small Tickets

- [x] [PR-168A — Environment notification internal API](PR-168A-environment-notification-internal-api.md).
- [x] [PR-168B — Environment notification dispatch lease](PR-168B-environment-notification-dispatch-lease.md).
- [x] [PR-168C — Environment notification subscriber cutover](PR-168C-environment-notification-subscriber-cutover.md).
- [x] [PR-168D — Runtime Environment notification finalization](PR-168D-runtime-environment-notification-finalization.md).
- [ ] PR-168E — Remove message-lifecycle/outbox notification compatibility and guard it.

## Done Criteria

- Agent loop trigger ownership is Environment notification lifecycle.
- UI read/delivered status and message storage no longer influence agent loop state.
- Failures preserve retryable notification state; no user message is silently lost.
