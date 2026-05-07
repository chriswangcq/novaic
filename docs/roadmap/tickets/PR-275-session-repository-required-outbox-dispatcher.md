# PR-275 — SessionRepository Required Outbox Dispatcher

Status: Closed

## Goal

Make `SessionOutboxDispatcher` an explicit required dependency of
`SessionRepository`.

## Why

After wake creation and attach delivery moved to durable outbox, the session
coordinator cannot operate correctly without an outbox dispatcher. Keeping
`outbox_dispatcher: ... | None = None` leaves a false optional path and makes
future changes look allowed to bypass durable publication.

## Scope

- Change `SessionRepository.__init__` to require a
  `SessionOutboxDispatcher`.
- Remove `None` guard branches around attach/wake outbox publication.
- Keep exception handling for deferred publication failures.
- Add guard coverage that the repository no longer exposes an optional outbox
  dispatcher dependency.

## Non-Goals

- Do not change outbox dispatcher internals.
- Do not change durable outbox table schema.
- Do not change session dispatch or finalize behavior.

## Acceptance Criteria

- `SessionRepository` constructor type requires `SessionOutboxDispatcher`.
- `session_repo.py` contains no `outbox_dispatcher is None` branch.
- Runtime startup and tests continue passing with explicit dispatcher wiring.
- Targeted session tests pass.
- Full `novaic-agent-runtime` test suite passes.
- `git diff --check` is clean.

## Closure Notes

- Made `SessionOutboxDispatcher` a required `SessionRepository` constructor
  dependency.
- Removed dead `outbox_dispatcher is None` branches from session outbox
  publication paths.
- Updated the strict input-ledger failure test to pass an explicit exploding
  dispatcher, proving input ledger failure occurs before outbox publication is
  touched.
- Added `tests/test_pr275_session_repository_required_outbox_dispatcher.py`.
- Targeted tests passed: 6 passed.
- Full `novaic-agent-runtime` test suite passed: 320 passed.
