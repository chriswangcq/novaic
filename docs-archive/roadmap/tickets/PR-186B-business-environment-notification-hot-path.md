# PR-186B — Business Environment Notification Hot-Path Acceptance

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


Status: `[closed]` — 2026-05-03

## Analysis

Business owns Environment storage/service and the internal IM/notification APIs. Dedicated Environment entities are already present, and message rows are now UI projection, not the agent-loop source.

The gap is an acceptance guard that states the hot path directly: Environment writes event/message/notification records, notification state is independent of chat message lifecycle, and read/history APIs return bounded Environment percepts.

## Scope

- Add Business acceptance tests for Environment IM creation, notification state, and internal read/reply/send APIs.
- Guard that Environment notification lifecycle does not depend on `messages` / old `message_outbox` state.
- Keep chat `messages` projection explicitly product UI-only.

## Tests

- Business targeted pytest for Environment repository/API.
- Business full pytest before closure.

## Deployment / Git

- If only tests/docs change: no service deploy required.
- If Business behavior changes: deploy services and record smoke evidence.

## Closure

- Added `tests/test_pr186_environment_hot_path_acceptance.py`.
- Covered Environment event/message/notification writes, UI message projection as projection only, Environment-owned notification state transitions, and source guard against old loop storage.
- Tests:
  - `PYTHONPATH=. pytest -q tests/test_pr186_environment_hot_path_acceptance.py` → `3 passed`
  - `PYTHONPATH=. pytest -q` → `154 passed`
- No Business deploy required; no behavior changed.
