# PR-167B — Dedicated Environment Repository Read/Write Path

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
| Depends on | PR-167A |

## Goal

Move `EnvironmentRepository` reads/writes from `messages` wrappers onto the dedicated Environment entities introduced by PR-167A.

## Current-State Analysis

Before this ticket, `EnvironmentRepository` used `messages` as both chat transcript and Environment source of truth. That kept `chat_messages.lifecycle` coupled to Environment notification state and made `im_read` depend on the old message row shape.

The current App chat transcript and subscriber outbox still use `messages`, so this ticket keeps a deliberately named chat/outbox projection while moving Environment read APIs to `environment-*` entities. The projection is not a fallback; PR-168/169 will remove its remaining ownership once queue and App surfaces cut over.

## Implementation Checklist

- [x] `EnvironmentRepository.create_im_message` writes:
  - `environment-events`
  - `environment-im-messages`
  - `environment-notifications` when recipient is agent/subagent
- [x] `EnvironmentRepository.get_message` reads `environment-im-messages`, not `messages`.
- [x] `EnvironmentRepository.get_notification` and transitions read/write `environment-notifications`, not `chat_messages.lifecycle`.
- [x] Current user-message send path mirrors the created chat row into Environment with the same message id.
- [x] Current subagent spawn path mirrors the initial `SUBAGENT_SEND` row into Environment with the same message id.
- [x] Current `im_reply` / `im_send` routes continue publishing `messages` only as chat/outbox projection.
- [x] `messages.clear` removes Environment projection rows for the agent.
- [x] Unit tests cover dedicated repo writes, reads, notification state transitions, user send projection, route behavior, and subagent spawn projection.
- [x] Deploy Business and record evidence.

## Verification

- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_repository.py tests/test_environment_internal_api.py tests/test_environment_message_actions_projection.py tests/test_environment_schema_contracts.py tests/test_pr124_subagent_spawn_im.py` → 25 passed, 2 warnings.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q` → 203 passed, 2 warnings.
- `./deploy business` restarted all backend services successfully.
- `./deploy status` showed Entangled, Gateway, Business, Device, Queue, Storage, Cortex, workers, and Relay healthy.
- Production Python smoke verified `EnvironmentRepository.create_im_message` writes `environment-events`, `environment-im-messages`, and `environment-notifications`, then reads back from `environment-im-messages`.

## Completion Notes

Environment now has a dedicated source-of-truth repository. Remaining `messages` usage in this slice is explicitly projection for current Chat UI and subscriber outbox, to be removed by PR-168/169.
