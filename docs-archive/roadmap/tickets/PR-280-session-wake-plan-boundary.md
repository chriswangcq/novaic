# PR-280 — Session Wake Plan Boundary

Status: Closed

## Goal

Extract deterministic wake start/restart planning from `SessionRepository` into
a pure helper module.

## Scope

- Add a pure `session_wake_plan` module.
- Move saga context/idempotency/effective trigger/create-wake outbox effect
  shaping for dispatch start and pending restart into that module.
- Keep actual outbox append/publish in infrastructure.

## Acceptance Criteria

- `session_repo.py` no longer imports `TriggerType`,
  `build_create_wake_saga_effect`, or `build_pending_restart_saga`.
- Wake start/restart behavior stays unchanged.
- Pure plan tests cover recovered dispatch and pending restart context shaping.
- Full runtime suite passes.

## Verification

- Targeted PR-280 test.
- `pytest`
- `git diff --check`

## Closure Notes

- Added pure `queue_service/session_wake_plan.py`.
- Dispatch start planning now returns explicit effective trigger, metadata,
  saga context, idempotency key, and create-wake outbox effect.
- Pending restart planning now returns explicit pending metadata, saga context,
  idempotency key, and create-wake outbox effect.
- `SessionRepository` no longer imports `TriggerType`,
  `build_create_wake_saga_effect`, or `build_pending_restart_saga`.
- Added `tests/test_pr280_session_wake_plan_boundary.py`.
- Targeted wake start/restart tests passed: 12 passed.
