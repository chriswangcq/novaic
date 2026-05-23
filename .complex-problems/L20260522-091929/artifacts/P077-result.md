# Queue Production Postgres Cutover Result

## Summary

Completed the production Queue cutover from `/opt/novaic/data/queue.db` to Postgres `novaic_queue`. The cutover code was committed and deployed, production writers were inventoried and frozen, the final SQLite backup was archived with checksum, data was migrated and independently verified, Queue services restarted in Postgres mode, production smokes passed after the connection-pool lifecycle fix, and the old SQLite active path was archived as rollback-only with central cleanup notes updated.

## Done

- P121 committed, pushed, and deployed the Queue Postgres cutover runtime code to the API host.
- P122 inventoried production Queue processes, active SQLite holders, Postgres target readiness, and cutover preconditions.
- P123 froze Queue writers/workers and created the final backup under `/opt/novaic/backups/queue-cutover/20260523T011125Z`.
- P124 migrated the frozen SQLite backup into production Postgres `novaic_queue`, copying 25721 rows across 16 tables with zero independent verification mismatches.
- P125 restarted Queue Service and related worker/outbox/scheduler/subscriber processes from the clean cutover runtime in Postgres mode.
- P126 ran production health, API, task, saga, idempotency, session, worker/outbox, scheduler/subscriber, log, and holder smokes; after fixing a Postgres connection-pool lifecycle issue, smokes passed.
- P127 archived `/opt/novaic/data/queue.db` and sidecars out of the active path, verified no holders remained, and updated central SQLite classification plus Queue rollback/retention notes through follow-up P135.

## Verification

- Child checks `C133`, `C134`, `C139`, `C143`, `C144`, `C145`, and `C148` are all success.
- Freeze backup SHA256 for `queue.db` is `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`; the archived active-path SQLite copy matches this checksum.
- Migration final report status was validated and independent verification found no count, semantic, or consistency mismatches.
- Queue `/health` reports Postgres and `/ready` returns HTTP 200 after restart, smoke tests, and old SQLite archive.
- Process role counts after the pool fix include Queue Service, task workers, saga workers, session outbox, saga outbox, health, scheduler, subscriber, and gateway-facing process coverage.
- `/opt/novaic/data/queue.db`, `queue.db-wal`, and `queue.db-shm` no longer exist in the live data path, and lsof reported no holders after cleanup.
- Central cleanup notes now classify Queue SQLite as archived/rollback-only non-current state, name Postgres `novaic_queue` as source of truth, and retain rollback artifacts through `2026-06-22 Asia/Shanghai`.

## Known Gaps

- The legacy production runtime checkout `/opt/novaic/services/novaic-agent-runtime` remains dirty and should not be used for Queue runtime; production Queue now runs from `/opt/novaic/services/novaic-agent-runtime-pg`.
- Remote rollback artifacts are intentionally retained through the stabilization window; later retirement needs a separate explicit cleanup decision.
- Other service SQLite owners in the parent Postgres-unification ledger remain out of this Queue cutover scope.

## Artifacts

- Child result IDs: `R118`, `R119`, `R124`, `R128`, `R129`, `R130`, `R131`, `R132`
- Child check IDs: `C133`, `C134`, `C139`, `C143`, `C144`, `C145`, `C148`
- Freeze/backup: `.complex-problems/L20260522-091929/artifacts/queue-freeze-backup-report.json`
- Migration: `.complex-problems/L20260522-091929/artifacts/queue-production-migration-execution-report.json`
- Independent verification: `.complex-problems/L20260522-091929/artifacts/queue-production-migration-independent-verification-report.json`
- Restart: `.complex-problems/L20260522-091929/artifacts/queue-restart-postgres-report.json`
- Smoke: `.complex-problems/L20260522-091929/artifacts/queue-production-postgres-smoke-report.json`
- SQLite archive: `.complex-problems/L20260522-091929/artifacts/queue-sqlite-archive-report.json`
- Cleanup notes: `.complex-problems/L20260522-091929/artifacts/queue-cleanup-notes-update-report.json`
