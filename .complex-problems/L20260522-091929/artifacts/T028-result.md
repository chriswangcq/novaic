# T028 Result - Gateway Production Cutover Preflight

## Summary

Completed Gateway production cutover preflight. Gateway remains on SQLite, but the Postgres target is reachable, the DSN file is prepared with restrictive permissions, `psycopg` is available in the remote Gateway venv, source counts are captured, and a migration script is prepared for P032.

## Artifact

- `.complex-problems/L20260522-091929/artifacts/gateway-production-preflight.md`

## Preflight Evidence

- Current Gateway process has no Postgres backend flags.
- Gateway health remains healthy.
- Source SQLite counts:
  - `users=1`
  - `refresh_tokens=26`
  - `config=5`
- Target Postgres connectivity:
  - `pg_connect=ok db=novaic_gateway user=novaic_gateway`
- Target public tables:
  - `<none>`
- DSN file:
  - `/opt/novaic/postgres/secrets/novaic_gateway_dsn`
  - mode `600`, owner `root:root`
- Remote venv dependency:
  - `psycopg_import=ok:3.3.4`
- Migration script prepared:
  - `novaic-gateway/scripts/migrate_gateway_sqlite_to_postgres.py`

## Notes

- The first DSN format was invalid because the generated password contains URL-sensitive characters. It was rewritten using psycopg's key/value DSN builder and then verified.
- The remote Gateway venv's own `pip` is incomplete. `psycopg` was installed into the venv site-packages via system pip `--target`.

## No-Cutover Statement

This ticket did not restart Gateway, deploy the new code, copy production rows, or switch runtime backend. P032 remains the production execution step.
