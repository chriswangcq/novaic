# Queue Production Migration Independent Verification Report

## Summary

- Status: success
- Source SQLite backup: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db`
- Target database: `novaic_queue`
- Row count mismatches: 0
- Semantic mismatches: 0
- Consistency mismatches: 0

## Row Counts

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

## Consistency Checks

- Tasks without state: 0
- Task state rows without task projection: 0
- Sagas without state: 0
- Saga state rows without saga projection: 0
- Completed idempotency rows without task: 0
- Pending task state rows: 23

## Artifacts

- Remote verification report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-migration-independent-verification-report.json`
- Local verification report: `.complex-problems/L20260522-091929/artifacts/queue-production-migration-independent-verification-report.json`
