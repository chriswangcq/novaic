# Queue Postgres Post-Smoke Counts Result

## Summary

Recorded post-smoke Queue Postgres counts and redacted target public info after the successful API smoke run `20260522T165950Z-74bc8a64`.

## Done

- Re-queried the staging Postgres container from `api.gradievo.com`.
- Wrote a redacted count report to `.complex-problems/L20260522-091929/artifacts/queue-post-smoke-count-report.json`.
- Tied the count report to the successful smoke report `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`.
- Recorded target identity without raw DSN or internal key exposure.

## Verification

- Count report generation returned `ok=true`, `count_keys=16`, `histogram_keys=6`.
- Target public info:
  - host alias `api.gradievo.com`;
  - container `novaic-queue-staging-postgres`;
  - container health `healthy`;
  - host bind `127.0.0.1:15432`;
  - database/user `novaic_queue_staging`;
  - DSN file path `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`;
  - secret marked `redacted`.
- Key counts:
  - `config_version=18`;
  - `tq_tasks=2`;
  - `tq_task_events=6`;
  - `tq_task_state=2`;
  - `tq_sagas=2`;
  - `tq_saga_events=7`;
  - `tq_saga_state=2`;
  - `tq_worker_lease_events=8`;
  - `tq_worker_lease_state=4`;
  - `tq_idempotency_ledger=1`;
  - `tq_session_events=6`;
  - `tq_session_state=1`;
  - `tq_session_outbox=2`.
- Histograms:
  - `task_status_done=1`;
  - `task_status_failed=1`;
  - `saga_status_completed=1`;
  - `saga_status_failed=1`;
  - `session_state_starting=1`;
  - `session_outbox_pending=2`.

## Known Gaps

- Counts include staging smoke rows and are not production metrics.
- Some empty outbox tables remain `0`, which is expected for this smoke shape.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-post-smoke-count-report.json`
- `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`
