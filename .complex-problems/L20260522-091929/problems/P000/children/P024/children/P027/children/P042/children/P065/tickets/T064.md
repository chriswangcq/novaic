# Restart Production Entangled In Postgres Mode

## Problem Definition

Production Entangled has been migrated into Postgres, but the live process still serves from SQLite. The production process must be restarted on the existing loopback port `19900` using Postgres and file-based secrets, with no active SQLite holders afterward.

## Proposed Solution

Stop the existing SQLite-mode Entangled process, start Entangled from the deployed package using the production venv with `--db-backend postgres`, `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`, and `--service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`, write logs/PID under `/opt/novaic`, wait for health/readiness, inspect process args for file-based secrets, verify no `/opt/novaic/data/entangled.db*` holders remain, and record rollback commands to stop the PG process and relaunch the SQLite command from the `P063` backup/freeze report if needed.

## Acceptance Criteria

- Previous SQLite-mode Entangled process is stopped.
- New production Entangled process listens on `127.0.0.1:19900`.
- New process uses `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.
- Process args contain no raw DSN or raw service-token values.
- `/v1/health` and `/v1/ready` return HTTP 200.
- No process holds `/opt/novaic/data/entangled.db*`.
- Rollback command/path is recorded.
- Business API/subscriber remain frozen for `P066` smokes and later restart.

## Verification Plan

Use sanitized process inspection, `ss`, `lsof`, health/readiness HTTP calls, and log tail checks. Do not print raw DSN/token values. Record a redacted runtime report in the ledger artifacts.

## Risks

- If the PG-mode process fails readiness, rollback must be available before moving SQLite files.
- Direct process launch must use the correct `PYTHONPATH` so the deployed Postgres-capable Entangled package is used.
- Business API/subscriber are still down until later steps complete.

## Assumptions

- `P064` migration succeeded and `novaic_entangled` has the production data.
- `P063` prepared `entangled_production_service_token`.
- The existing production port `19900` should remain the public local target for Gateway/Business.
