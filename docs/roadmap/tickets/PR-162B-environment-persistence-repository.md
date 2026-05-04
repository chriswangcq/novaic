# PR-162B — Environment Persistence Repository and Migrations

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-162 |
| Repos | `novaic-business`, `novaic-common`, docs |
| Depends on | PR-162A |

## Goal

Create the Environment persistence layer and repository API without switching the live agent loop.

The repository should be able to represent event envelopes, IM messages, notifications, and resource refs. It may wrap existing `chat_messages`/outbox behavior during transition, but it must expose Environment terminology and tests.

## Implementation Plan

1. Inspect whether to introduce new tables immediately or wrap existing `chat_messages`/outbox behind a repository first.
2. Add repository methods for create/read IM message, read notification projection, validate notification transitions, and validate resource refs.
3. Keep live hot paths unchanged; this ticket introduces the boundary but does not switch callers.
4. Add tests proving canonical message shape and strict rejection of non-canonical raw content.

## Current-State Analysis

Completed 2026-05-02.

Decision: PR-162B wraps existing `chat_messages` as the first persistence substrate instead of introducing new tables immediately.

Reason:

- Existing `chat_messages` already has the fields needed for IM message storage and dispatch lifecycle.
- `message_outbox` is already generated transactionally by Entangled append for triggerable message types.
- A table rename or live schema split at this stage would touch subscriber, Queue, Runtime session.init, and Context read at once, creating exactly the kind of branch entropy this project is trying to avoid.
- The repository therefore establishes Environment vocabulary and strict shape first. Later tickets can migrate callers behind it, then decide whether separate Environment tables are still useful.

Important finding:

- Existing `SUBAGENT_SEND` hot code still writes raw string content in some paths. The new repository intentionally rejects raw string content instead of adding a compatibility branch. This is a future cutover requirement, not something PR-162B hides.

## Tests

- Unit: `PYTHONPATH=.:../novaic-common pytest tests/test_environment_repository.py` — 10 passed.
- Regression smoke: `PYTHONPATH=.:../novaic-common pytest tests/test_environment_repository.py tests/test_pr160_message_content_shape.py tests/test_bulk_transition.py` — 18 passed, 1 existing Pydantic deprecation warning.
- Full Business collection note: current local full-suite collection is blocked by an existing `tests.*` package-shadowing issue outside PR-162B (`novaic-cortex/tests` or `novaic-agent-runtime/tests` can shadow Business `tests`). This ticket did not modify that path.

## Smoke / Deploy / Git

- Smoke: synthetic Environment message and notification projections are covered by `tests/test_environment_repository.py`.
- Deploy: `./deploy business` — all backend services restarted successfully.
- Production smoke: remote import and transition validation returned `environment_repository_ok`.
- Git: `novaic-business` commit `045d86f feat(business): add environment repository boundary`.

## Done Criteria

- [x] Repository API exists and is covered.
- [x] Storage semantics are explicit and strict.
- [x] Existing chat/subagent behavior remains unchanged.

## Evidence

- Files added:
  - `business/environment.py`
  - `tests/test_environment_repository.py`
- `business/environment.py` introduces `EnvironmentRepository`, `EnvironmentMessage`, `EnvironmentNotification`, and `EnvironmentResourceRef`.
- No live runtime or API caller was switched in this ticket.
