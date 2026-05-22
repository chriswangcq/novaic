# Queue Service API Smoke Success Check

## Summary

`P112` is successful. `R112` exercised the real staging Queue Service in Postgres mode across health, readiness, task lifecycle, saga lifecycle, session dispatch/finalize, idempotency, and post-smoke database counts. No operation was skipped.

## Evidence

- Final smoke report: `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`.
- Smoke report `ok=true`, operation count `26`, skips `[]`.
- Staging service endpoint: `http://127.0.0.1:19987`.
- Internal key was used by the smoke script without printing it.
- Post-smoke counts show writes landed in Postgres tables:
  - `tq_tasks=2`;
  - `tq_task_state=2`;
  - `tq_sagas=2`;
  - `tq_saga_state=2`;
  - `tq_session_events=6`;
  - `tq_session_state=1`;
  - `tq_session_outbox=2`;
  - `tq_idempotency_ledger=1`.
- Focused regression tests for discovered Postgres JSONB binding defects passed: `49 passed in 0.14s`.

## Criteria Map

- Health/readiness smoke passes: satisfied by operations `health` and `ready`.
- Task publish/claim/complete/fail passes: satisfied by task complete and task fail operation groups.
- Saga create/claim/launch/complete/fail passes: satisfied by saga complete and saga fail operation groups.
- Session dispatch/finalize/rebuild or safe equivalent passes: satisfied by `session_dispatch`, `session_ended`, sessions diagnostics, pending diagnostics, and the earlier startup rebuild evidence from `P111`.
- Idempotency duplicate/in-progress/completed-result passes: satisfied by idempotency acquire duplicate and completed replay operations.
- Skipped operations have explicit reasons: no skipped operations.

## Execution Map

- `R112` contains the smoke execution, discovered Postgres JSONB fixes, focused tests, remote deployment, final smoke report, and DB counts.

## Stress Test

- The smoke used real HTTP calls against the api-host service and real Postgres writes, not mocked repositories.
- The run included both success and terminal-failure paths for tasks and sagas plus duplicate idempotency contention.

## Residual Risk

- The smoke rows remain in the dedicated staging database; this is acceptable for test evidence and can be cleaned in a later staging maintenance task if desired.
- Local code fixes still need commit/push.

## Result IDs

- `R112`
