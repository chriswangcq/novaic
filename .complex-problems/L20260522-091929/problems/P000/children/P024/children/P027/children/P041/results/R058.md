# Entangled Production Postgres Cutover Preflight Result

## Summary

`T060` completed the production Entangled Postgres cutover preflight on `api.gradievo.com` without switching the production runtime. Current production Entangled is healthy/ready on SQLite, the source SQLite inventory and semantic counts were captured, active SQLite file holders were identified, the production Postgres target DSN secret was created and verified, deployed migration/runtime imports passed, and a rollback directory was prepared.

## Done

- Captured sanitized production runtime state:
  - process on `127.0.0.1:19900`.
  - SQLite path `/opt/novaic/data/entangled.db`.
  - no Postgres backend flag active.
  - legacy raw service-token argument detected but not printed.
- Captured production health/readiness:
  - `/v1/health`: HTTP 200, 22 entities.
  - `/v1/ready`: HTTP 200, 22 entities, no missing entities.
- Captured SQLite source snapshot:
  - SQLite file exists, size 7,106,560 bytes, mode `644 root:root`.
  - 28 application tables.
  - `entangled_sync_versions`: 67 rows, max version 5319.
  - `subagent_state_transitions`: 184 rows, max ID 542.
  - 21 active SQLite file handles held by the production Entangled process.
- Prepared and verified production Postgres DSN secret:
  - `/opt/novaic/postgres/secrets/novaic_entangled_dsn`.
  - mode `600 root:root`.
  - connects as `novaic_entangled` to database `novaic_entangled`.
  - target public table count: 0.
- Verified deployed code on the API host:
  - `entangled.app.main` import: ok.
  - `entangled.sql.migration` import: ok.
  - `entangled.sql.migration_cli` import: ok.
  - `psycopg` and `psycopg_pool` imports: ok.
  - remote Entangled package compile: ok.
  - migration CLI `--help`: ok.
- Prepared rollback archive directory:
  - `/opt/novaic/residue-archive/entangled-cutover-preflight-20260522T105730Z`.

## Verification

- Redacted report written at `.complex-problems/L20260522-091929/artifacts/entangled-production-cutover-preflight-report.json`.
- Post-preflight production runtime still uses `/opt/novaic/data/entangled.db`; no runtime switch occurred.
- No raw DSN/password/service-token values are stored in the report.

## Known Gaps

- Production Entangled still passes the service token as a raw process argument. The cutover should switch to `--service-token-file`.
- Production SQLite has active file holders, as expected; the actual cutover must stop/restart writers in a controlled window.
- This is preflight only. It does not import production data into Postgres or restart production Entangled.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-production-cutover-preflight-report.json`
