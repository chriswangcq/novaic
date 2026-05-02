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
- PR-168B — Queue/subscriber claims Environment notifications, not message rows.
- PR-168C — Runtime finalization marks Environment notifications processed/failed.
- PR-168D — Remove message-lifecycle notification compatibility and guard it.

## Done Criteria

- Agent loop trigger ownership is Environment notification lifecycle.
- UI read/delivered status and message storage no longer influence agent loop state.
- Failures preserve retryable notification state; no user message is silently lost.
