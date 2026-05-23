# Queue Production Migration Execution Report

## Summary

- Status: validated
- Runtime commit: `0517c37ae0c3368ec9c2a87fd6270f3e28603289`
- Source SQLite backup: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db`
- Target database: `novaic_queue`
- Total copied rows: 25721
- Migration errors: none

## Copied Rows

- `config`: 1
- `tq_tasks`: 2247
- `tq_task_events`: 6996
- `tq_task_state`: 2247
- `tq_task_outbox`: 0
- `tq_sagas`: 315
- `tq_saga_events`: 3226
- `tq_saga_state`: 315
- `tq_saga_outbox`: 6
- `tq_worker_lease_events`: 5379
- `tq_worker_lease_state`: 2539
- `tq_worker_lease_outbox`: 0
- `tq_idempotency_ledger`: 2215
- `tq_session_events`: 202
- `tq_session_state`: 2
- `tq_session_outbox`: 31

## Semantic Aggregates

- Schema version: source `18`, target `18`
- Task states: `done=2215`, `failed=9`, `pending=23`
- Saga states: `completed=309`, `failed=6`
- Session states: `no_active=2`
- Idempotency statuses: `completed=2215`
- Worker lease states: `released=2539`
- Published saga outbox rows: 6
- Published session outbox rows: 31

## Artifacts

- Remote migration report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-migration-execution-report.json`
- Remote reset report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-migration-execution-reset-report.json`
- Local migration report: `.complex-problems/L20260522-091929/artifacts/queue-production-migration-execution-report.json`
- Local reset report: `.complex-problems/L20260522-091929/artifacts/queue-production-migration-execution-reset-report.json`

## Notes

- The first execution attempt exposed a JSONB adapter gap before data copy completed. The code was fixed in commit `0517c37ae0c3368ec9c2a87fd6270f3e28603289`, the empty target tables were reset, and the migration was rerun successfully.
- The final migration report status is `validated`, which includes source-to-target row count and semantic aggregate validation.
