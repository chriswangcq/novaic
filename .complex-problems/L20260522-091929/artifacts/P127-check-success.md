# Queue SQLite Archive And Cleanup Notes Success Check

## Summary

`P127` is successful after follow-up `P135`. Result `R131` archived the active Queue SQLite path and verified Postgres health/ready with no SQLite holders; result `R132` updated the central SQLite classification and rollback documentation with a retention policy and sanitized local evidence.

## Evidence

- `R131` archived `/opt/novaic/data/queue.db`, `queue.db-wal`, and `queue.db-shm` under `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z/`.
- `R131` verified live SQLite paths are absent, Queue `/health` reports Postgres, Queue `/ready` returns HTTP 200, and `lsof` has no Queue SQLite holders after archive.
- `R131` recorded archived `queue.db` SHA256 `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`, matching the final freeze backup.
- `R132` updated the central classification so Queue SQLite is `archived/rollback-only non-current SQLite snapshot` and current state owner is Postgres `novaic_queue`.
- `R132` created the Queue rollback note with archive path, checksum, runtime facts, intentional restore expectation, and retention through `2026-06-22 Asia/Shanghai`.
- Local artifacts from both results were scanned for credential patterns, with final scans clean for the relevant report/note artifacts.

## Criteria Map

- `/opt/novaic/data/queue.db` moved or marked rollback-only: satisfied by `R131` archive action and `R132` classification update.
- No production process holds old SQLite after cleanup: satisfied by `R131` lsof after archive with no holder PIDs.
- Central SQLite classification and rollback notes updated to say Queue runtime source of truth is Postgres: satisfied by `R132`.
- Cleanup preserves final backup and checksum: satisfied by `R131` archived SHA256 matching the freeze backup and `R132` rollback note.
- Report states whether rollback-only SQLite can be retired or retained for a defined window: satisfied by `R132` retention through `2026-06-22 Asia/Shanghai` and explicit later cleanup requirement.

## Execution Map

- `R131` performed active-path archive, health/ready/lsof verification, checksum capture, and local cleanup report capture.
- `R132` closed the previous documentation gap by updating remote notes, adding rollback/retention policy, copying sanitized local evidence, and verifying with report checks.

## Stress Test

- Plausible failure mode: stale code silently falls back to `/opt/novaic/data/queue.db`. Coverage: live path and sidecars are absent, no process holds the file, and central notes no longer present Queue SQLite as active.
- Plausible failure mode: rollback artifacts are preserved but operationally ambiguous. Coverage: rollback note defines intentional restore steps and a retention/retirement policy.
- Plausible failure mode: documentation says Postgres but service is unhealthy. Coverage: `R131` verified health backend Postgres and readiness HTTP 200 after archive.

## Residual Risk

- Rollback now requires an intentional restore of archived SQLite and explicit runtime switch; that is documented and non-blocking.
- Other service SQLite work remains in parent ledger scope and does not block Queue cleanup closure.

## Result IDs

- R131
- R132
