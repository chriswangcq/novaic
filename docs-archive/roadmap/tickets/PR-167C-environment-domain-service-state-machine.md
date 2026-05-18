# PR-167C — Environment Generic Event API and Lifecycle State Machine

> Historical ticket archive: this closed ticket predates the PR-229 chat
> projection cleanup. `chat_messages.lifecycle` references here are archaeology,
> not current architecture.

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-167 |
| Repos | `novaic-business`, docs |
| Depends on | PR-167B |

## Goal

Complete Environment as a testable domain service rather than an IM-only helper.

## Current-State Analysis

PR-167B moved IM repository reads/writes to dedicated Environment entities, but the service still lacked a generic event/notification API for non-IM stimuli such as system events, external events, and resource events. Without that API, later Queue/Subscriber cutover would be tempted to grow one-off paths.

## Implementation Checklist

- [x] Add `EnvironmentEvent` domain model.
- [x] Add `create_event(...)` with event kind and sender validation from the Common contract.
- [x] Add `get_event(...)`.
- [x] Add `create_notification(...)`.
- [x] Add `list_notifications(...)` with state and recipient filtering.
- [x] Keep notification transitions in Environment state, independent from `chat_messages.lifecycle`.
- [x] Expose the generic APIs through `EnvironmentService`.
- [x] Unit tests cover generic event creation, notification creation/listing, invalid event rejection, and lifecycle transitions.
- [x] Deploy Business and record evidence.

## Verification

- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_repository.py tests/test_environment_internal_api.py tests/test_environment_message_actions_projection.py tests/test_pr124_subagent_spawn_im.py` → 23 passed, 2 warnings.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q` → 206 passed, 2 warnings.
- `./deploy business` restarted all backend services successfully.
- `./deploy status` showed Entangled, Gateway, Business, Device, Queue, Storage, Cortex, workers, and Relay healthy.
- Production Python smoke verified generic `create_event`, `create_notification`, and `list_notifications` behavior.

## Completion Notes

Environment now has a generic event + notification state-machine API. Remaining lifecycle coupling is in the queue/session hot path, tracked by PR-168.
