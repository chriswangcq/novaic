# Queue Postgres Cutover And Rollback Note

Generated: 2026-05-23 10:17 Asia/Shanghai
Host: api.gradievo.com

## Current Source Of Truth

Queue runtime source of truth is Postgres database `novaic_queue`.

Production Queue runs from `/opt/novaic/services/novaic-agent-runtime-pg` at commit `c7aa54517e84ffd6ed931c9f1f8b9c120b6343e9` with backend `postgres` and DSN file `<redacted-credential-path>`. The old SQLite active path `/opt/novaic/data/queue.db` must not be treated as current runtime state.

## Cutover Evidence

- Final frozen SQLite backup: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db`
- Final backup SHA256: `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`
- Migration target: Postgres database `novaic_queue`
- Migration copied rows: 25721 across 16 Queue tables
- Independent verification: no count, semantic, or consistency mismatches
- Post-cutover health: `/health` reported `database_backend=postgres`
- Post-cutover readiness: `/ready` returned HTTP 200
- Production smoke: task, saga, idempotency, session, worker lease, outbox, scheduler, subscriber, and gateway paths passed
- SQLite live-path holders after cutover: none

## Archived SQLite Rollback Files

Archive directory: `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z`

| File | Size | SHA256 |
|---|---:|---|
| `queue.db` | 378683392 | `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153` |
| `queue.db-wal` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `queue.db-shm` | 32768 | `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` |

The live paths `/opt/novaic/data/queue.db`, `/opt/novaic/data/queue.db-wal`, and `/opt/novaic/data/queue.db-shm` were removed after Postgres health and smoke checks passed.

## Rollback Expectation

Rollback is now an intentional restore operation, not an accidental fallback path.

1. Stop Queue service, task workers, saga workers, outbox processors, scheduler, subscriber, and gateway-facing Queue clients.
2. Confirm no process uses Postgres Queue state during rollback.
3. Restore the archived `queue.db` from `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z` to `/opt/novaic/data/queue.db`.
4. Switch Queue runtime configuration back to SQLite explicitly.
5. Start Queue services and verify `/health`, `/ready`, task claim/complete, saga progression, session state, and outbox processing.
6. Record the rollback in the ledger and update this note before accepting traffic.

Do not copy the archived SQLite file back while Postgres Queue services are running.

## Retention And Retirement Policy

Retain the final freeze backup and archived active-path SQLite files through 2026-06-22 Asia/Shanghai. After that date, the artifacts may be retired only by a separate explicit cleanup ledger item that verifies Postgres backups, production stability, and no pending rollback need. Until such a cleanup is completed, the archived SQLite files remain rollback-only evidence.
