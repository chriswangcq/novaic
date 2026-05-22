# Gateway Production Cutover Preflight

Snapshot time: 2026-05-22 12:36 CST  
Host: `api.gradievo.com`  
Scope: P031 preflight and preparation only. No Gateway restart, backend switch, production data migration, or service config cutover was performed.

## Current Runtime

Gateway process is still running without Postgres backend flags:

```text
3473503 /opt/novaic/services/novaic-gateway/.venv/bin/python /opt/novaic/services/novaic-gateway/main_gateway.py --host 127.0.0.1 --port 19999 --data-dir /opt/novaic/data --queue-service-url http://127.0.0.1:19997 --blob-service-url http://127.0.0.1:19995 --blob-upload-url http://127.0.0.1:19995
```

Health remains healthy:

```json
{"status":"healthy","version":"0.3.0","agent_initialized":true,"mcp_healthy":false,"tools_count":0,"vmcontrol_healthy":false}
```

## Source SQLite Counts

Source file:

```text
/opt/novaic/data/gateway.db
```

Counts:

| table | rows |
|---|---:|
| users | 1 |
| refresh_tokens | 26 |
| config | 5 |

## Target Postgres Readiness

Target:

```text
database=novaic_gateway user=novaic_gateway
```

Connectivity check from the Gateway venv succeeded:

```text
pg_connect=ok db=novaic_gateway user=novaic_gateway
```

Current public target tables:

```text
<none>
```

This means P032 can create the Gateway tables cleanly through the deployed Postgres schema initializer or migration script.

## DSN File

Prepared DSN file:

```text
/opt/novaic/postgres/secrets/novaic_gateway_dsn mode=600 owner=root:root
```

The DSN file was first attempted as a URL, but the password contains characters that require escaping. It was rewritten using `psycopg.conninfo.make_conninfo()` key/value format, then verified by a live connection test. No credential value was printed.

## Dependency Readiness

Initial remote venv import check:

```text
psycopg_import=missing:ModuleNotFoundError
```

The Gateway venv's bundled `pip` was incomplete, so `python -m pip install` from that venv failed. Dependency was installed into the venv site-packages via system pip `--target`.

Final import check:

```text
psycopg_import=ok:3.3.4
```

## Migration Mechanics

Prepared local migration script:

```text
novaic-gateway/scripts/migrate_gateway_sqlite_to_postgres.py
```

Script behavior:

- reads `/opt/novaic/data/gateway.db`;
- reads `/opt/novaic/postgres/secrets/novaic_gateway_dsn`;
- creates only `users`, `refresh_tokens`, and `config` in Postgres through the Gateway Postgres schema;
- supports `--dry-run` and `--replace`;
- prints table row counts only, not row contents or secrets;
- fails if source and target row counts differ.

Local checks:

```text
python -m py_compile scripts/migrate_gateway_sqlite_to_postgres.py
tests/test_gateway_postgres_storage.py: 4 passed
```

## P032 Ready Steps

1. Back up `/opt/novaic/data/gateway.db`.
2. Deploy Gateway code changes including the migration script.
3. Run the migration script with `--replace`.
4. Update Gateway startup flags to include:
   - `--db-backend postgres`
   - `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_gateway_dsn`
5. Restart Gateway stack.
6. Verify health, auth/config smoke, Postgres counts, and no active SQLite writes.

## No-Cutover Statement

Gateway remains on its current SQLite runtime at the end of P031. P032 is the production cutover.
