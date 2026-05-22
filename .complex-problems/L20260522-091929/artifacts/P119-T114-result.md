# Queue Staging DSN Repair Result

## Summary

The staging DSN file on `api.gradievo.com` was regenerated in a libpq-safe URI form without printing the secret. The Queue Service startup moved past the previous host-resolution failure and connected to the intended loopback Postgres endpoint. Startup is still not successful because fresh Postgres schema initialization exposes a runtime code bug: after the expected missing `config` table probe fails, the transaction is not rolled back before running baseline DDL.

## Done

- Regenerated `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` from `/opt/novaic/queue-staging-postgres/postgres.env` using URL-encoded credentials.
- Preserved the DSN file as the secret source; the DSN contents were not printed in logs, chat, or artifacts.
- Confirmed DSN file mode is `0600`.
- Confirmed Docker container `novaic-queue-staging-postgres` health is `healthy`.
- Confirmed `pg_isready` reports Postgres accepting connections inside the container.
- Restarted staging Queue Service on `127.0.0.1:19987` with the DSN file and sibling `novaic-common` import path.
- Confirmed the previous parse failure is gone: logs now show connection attempts to `host=127.0.0.1 port=15432 database=novaic_queue_staging`.

## Verification

- Remote output:
  - `dsn_rewritten=1`
  - `dsn_target=127.0.0.1:15432/novaic_queue_staging`
  - `dsn_mode=600`
  - `container_health=healthy`
  - `pg_isready=/var/run/postgresql:5432 - accepting connections`
- Queue Service startup failure after DSN fix:
  - `psycopg.errors.InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block`
  - Failure occurs in `queue_service/db/schema.py:init_postgres_schema`.
- Diagnostic schema replay:
  - `POSTGRES_SCHEMA_STATEMENTS` completed in a clean debug schema: `schema_debug_ok=58`.
  - This indicates the baseline DDL is valid and the failure is caused by transaction state handling before the DDL loop.

## Known Gaps

- `init_postgres_schema` must roll back after the initial missing-`config` probe fails on a fresh Postgres database.
- After the code fix is deployed to the staging checkout, Queue Service must be restarted and `/health` plus `/ready` must pass.

## Artifacts

- Remote log: `/opt/novaic/queue-service-staging/queue-service.log`.
- Staging DSN file path: `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
- Diagnostic replay used `POSTGRES_SCHEMA_STATEMENTS` from `/opt/novaic/queue-service-staging/runtime/queue_service/db/schema.py`.
