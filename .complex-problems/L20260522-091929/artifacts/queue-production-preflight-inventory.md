# Queue Production Cutover Preflight Inventory

Generated: 2026-05-22 17:42 UTC / 2026-05-23 01:42 Asia/Shanghai

## Decision

Conditional go for the next freeze/backup child (`P123`) if the operator accepts a brief Queue writer freeze window. Do not migrate yet.

The production Queue target is still active on SQLite at `/opt/novaic/data/queue.db`, production Queue processes are identified, and production Postgres contains the intended `novaic_queue` database. The next safe action is to freeze the listed Queue writers/workers, archive the final SQLite backup, and then proceed to migration only if the backup and no-holder checks pass.

## Current Production Queue State

- Queue Service: `http://127.0.0.1:19997`
- `/health`: healthy, database path `/opt/novaic/data/queue.db`
- `/ready`: ok, sqlite check ok, session state/outbox checks ok
- Active SQLite queue file:
  - Path: `/opt/novaic/data/queue.db`
  - Size: `378683392` bytes
  - Mode: `0644`
  - mtime UTC: `2026-05-20T14:13:52.513230+00:00`
- `lsof /opt/novaic/data/queue.db`: active holders present.

## Queue Writers And Related Processes

These processes must be stopped or frozen before the final backup:

- `3533620` Queue Service, port `19997`, data dir `/opt/novaic/data`
- `3533685` task-worker, pool `control`
- `3533686` task-worker, pool `control`
- `3533687` task-worker, pool `execution`
- `3533688` task-worker, pool `execution`
- `3533689` saga-worker, max concurrent `4`
- `3533690` saga-worker, max concurrent `4`
- `3533691` session-outbox-worker
- `3533692` saga-outbox-worker
- `3533693` health worker
- `3533694` scheduler
- `3569211` business subscriber using Queue Service URL `19997`

Related service depending on Queue Service:

- `3533550` gateway using Queue Service URL `19997`

Staging-only Queue Service, not part of production freeze:

- `3617976` staging Queue Service, port `19987`, Postgres mode

## SQLite Holder Evidence

`lsof` reported active holders on `/opt/novaic/data/queue.db`:

- Queue Service PID `3533620` with multiple open file descriptors.
- session-outbox-worker PID `3533691`.
- saga-outbox-worker PID `3533692`.

This is expected before freeze and confirms that final backup must not run while these processes are active.

## Postgres Target Evidence

Docker containers:

- `novaic-postgres`, `postgres:16-alpine`, `127.0.0.1:5432->5432/tcp`, healthy
- `novaic-queue-staging-postgres`, `postgres:16-alpine`, `127.0.0.1:15432->5432/tcp`, healthy
- `novaic-llm-factory`, healthy

Production Postgres databases visible in `novaic-postgres`:

- `novaic_queue`
- `novaic_gateway`
- `novaic_cortex`
- `novaic_entangled`
- `novaic_entangled_rest_staging`
- `novaic_llm_factory`
- `postgres`

The intended production Queue target `novaic_queue` exists.

## Redaction

Credential values, connection strings, and credential-file paths were redacted in the JSON artifact and are not included in this report. The raw inventory script avoids printing credential file contents.

## Rollback Plan

- Before migration, stop/freeze queue writers and copy `/opt/novaic/data/queue.db` to a timestamped backup.
- If Postgres cutover fails before cleanup, stop Postgres-mode Queue services, restore config to sqlite mode, restore the backup over the active queue file, and restart the previous Queue Service/workers.
- Do not delete the SQLite backup during the cutover window.

## Next Gate

Proceed to `P123: Freeze Queue Writers And Archive Final SQLite Backup`. Required gate checks:

- Stop/freeze all listed Queue writers/workers.
- Confirm `lsof /opt/novaic/data/queue.db` has no active holders before or immediately after backup, depending on backup strategy.
- Create timestamped backup and checksum.
- Reconfirm no writer has restarted before migration.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-production-preflight-inventory.json`
