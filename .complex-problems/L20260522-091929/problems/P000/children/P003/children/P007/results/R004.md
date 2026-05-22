# T006 Result: LLM Factory Runtime Cut Over to Postgres

## Summary

Cut over the live `novaic-llm-factory` Docker runtime from SQLite to the `novaic_llm_factory` Postgres database. The container is healthy, reports `postgres` from its own config/backend path, no longer holds the SQLite DB open, and the old SQLite file is retained as rollback-only with explicit documentation.

## Done

- Backed up remote LLM Factory source files before deploying Postgres-capable code:
  - `/opt/novaic/llm-factory/source-backups/pre-postgres-cutover-20260522T015013Z`
- Synced Postgres-capable source/config dependency files to `/opt/novaic/llm-factory/app`.
- Created root-only DSN secret:
  - `/opt/novaic/llm-factory/secrets/postgres_dsn`
- Updated runtime config:
  - `/opt/novaic/llm-factory/data/config.json`
  - `database.backend=postgres`
  - `database.dsn_file=/run/secrets/postgres_dsn`
  - request/response body logging remains disabled.
- Updated compose to mount secrets read-only and join the Postgres Docker network:
  - `/opt/novaic/llm-factory/docker-compose.yml`
  - external network `novaic-postgres_default`
- Rebuilt `novaic/llm-factory:local`.
- Preflighted the new image against Postgres before restart.
- Reran the SQLite-to-Postgres migration immediately before restart:
  - latest snapshot `/opt/novaic/llm-factory/backups/llm_factory-pre-postgres-20260522T015309Z.db`
  - latest report `/opt/novaic/llm-factory/migration-reports/sqlite-to-postgres-20260522T015309Z.json`
- Recreated the live container with `docker compose up -d --force-recreate llm-factory`.
- Added rollback/cutover documentation:
  - `/opt/novaic/llm-factory/POSTGRES_CUTOVER.md`
  - `/opt/novaic/llm-factory/data/llm_factory.db.NON_CURRENT_POSTGRES_CUTOVER.md`
- Updated `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` so `llm_factory.db` is no longer listed as current state owner.

## Verification

- Container:
  - `novaic-llm-factory Up ... (healthy) 127.0.0.1:19990->19990/tcp`
- Runtime backend from inside the container:
  - `postgres`
  - `llm_logs` count from app backend path: `29760`
- HTTP health:
  - `http://127.0.0.1:19990/health` returned `{"status":"ok","service":"llm-factory"}`
- DB-backed API read:
  - service returned `models_from_service=376` for a real configured user.
- SQLite ownership:
  - `lsof -- /opt/novaic/llm-factory/data/llm_factory.db` returned no holders after cutover.
- Postgres counts:
  - `api_keys=6`
  - `models=771`
  - `user_keys=2`
  - `llm_logs=29760`
  - `request_body_nonempty=0`
  - `response_body_nonempty=0`
- Existing services:
  - `docker`, `novaic`, and `nginx` active.
  - `novaic-postgres` running healthy.
  - `https://api.gradievo.com/health` healthy.

## Known Gaps

- The old SQLite file is intentionally retained for rollback. It is now `0600 root:root` and labeled non-current.
- The compose file itself is not secret-bearing, but it is still world-readable; the DSN is stored separately in the root-only secret file.

## Artifacts

- Runtime config: `/opt/novaic/llm-factory/data/config.json`
- DSN secret: `/opt/novaic/llm-factory/secrets/postgres_dsn`
- Compose file: `/opt/novaic/llm-factory/docker-compose.yml`
- Cutover notes: `/opt/novaic/llm-factory/POSTGRES_CUTOVER.md`
- Rollback SQLite file: `/opt/novaic/llm-factory/data/llm_factory.db`
- Rollback marker: `/opt/novaic/llm-factory/data/llm_factory.db.NON_CURRENT_POSTGRES_CUTOVER.md`
- Latest migration snapshot: `/opt/novaic/llm-factory/backups/llm_factory-pre-postgres-20260522T015309Z.db`
- Latest migration report: `/opt/novaic/llm-factory/migration-reports/sqlite-to-postgres-20260522T015309Z.json`
