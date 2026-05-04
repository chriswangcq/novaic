# PR-167D — Environment Backfill and Message-Backed Repository Removal

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-167 |
| Repos | `novaic-business`, production data, docs |
| Depends on | PR-167C |

## Goal

Close PR-167 by ensuring historical chat rows have Environment records and by guarding against reintroducing repository reads from `messages`.

## Current-State Analysis

After PR-167B/167C, live code writes and reads Environment through dedicated `environment-*` entities. Production data still had historical `messages` rows with no matching `environment-im-messages` rows, which would tempt future code to add fallback reads from `messages`.

## Implementation Checklist

- [x] Scan production data shape by agent.
- [x] Backfill historical `messages` rows into:
  - `environment-events`
  - `environment-im-messages`
  - `environment-notifications` where the recipient is agent/subagent
- [x] Preserve message ids across backfill so notification/message refs remain stable.
- [x] Map historical `chat_messages.lifecycle` to Environment notification state for backfilled notifications.
- [x] Add a source guard proving `EnvironmentRepository` does not read or update `messages`.
- [x] Run focused and full Business tests.
- [x] Record production backfill evidence.

## Verification

- Production pre-scan showed:
  - `415f6cfd4e5b4a04911b66cb8ab2cad7`: 59 `messages`, 0 `environment-im-messages`
  - `canary_a_1`: 152 `messages`, 0 `environment-im-messages`
  - `canary_b_1`: 1 `messages`, 0 `environment-im-messages`
- Production backfill result: `created=212`, `skipped_existing=0`, `skipped_type=0`, `errors=0`.
- Production post-scan showed:
  - `415f6cfd4e5b4a04911b66cb8ab2cad7`: 59 `messages`, 59 `environment-im-messages`
  - `canary_a_1`: 152 `messages`, 152 `environment-im-messages`
  - `canary_b_1`: 1 `messages`, 1 `environment-im-messages`
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_repository.py` → 17 passed.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q` → 207 passed, 2 warnings.

## Completion Notes

The remaining `messages` entity is now a chat/outbox projection, not the Environment repository backing store. The next ownership cut is PR-168: Queue/Subscriber should consume Environment notifications instead of `message_outbox` / `chat_messages.lifecycle`.
