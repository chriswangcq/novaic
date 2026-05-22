# Cortex Production Cutover Preflight

Snapshot time: 2026-05-22 12:55 CST  
Host: `api.gradievo.com`  
Scope: P035 preflight and preparation only. No Cortex restart, backend switch, production data migration, or service config cutover was performed.

## Current Runtime

Cortex process is still running with SQLite operational state:

```text
/opt/novaic/services/novaic-cortex/.venv/bin/python -m novaic_cortex.main_cortex ... --operational-sqlite-path /opt/novaic/data/cortex/operational.sqlite3 --redis-url redis://127.0.0.1:6379/0 --redis-lock-ttl-seconds 300
```

Readiness:

```json
{"status":"ok","checks":{"registry":"ok","blob_service":"ok","scope_locks":{"backend":"redis"}}}
```

## Source SQLite Counts

Source file:

```text
/opt/novaic/data/cortex/operational.sqlite3
```

Counts:

| table | rows |
|---|---:|
| cortex_operational_meta | 1 |
| scope_events | 25 |
| scope_projection | 26 |
| active_stack_projection | 5 |
| payload_manifest | 90 |

## Target Postgres Readiness

Target:

```text
database=novaic_cortex user=novaic_cortex
```

Connectivity check:

```text
cortex_dsn=ok db=novaic_cortex user=novaic_cortex
```

Current public target tables:

```text
<none>
```

## DSN File

Prepared DSN file:

```text
/opt/novaic/postgres/secrets/novaic_cortex_dsn mode=600 owner=root:root
```

The file was generated using `psycopg.conninfo.make_conninfo()` key/value format so password characters are escaped safely. No credential value was printed.

## Dependency Readiness

Initial Cortex venv import check:

```text
cortex_venv_psycopg=missing:ModuleNotFoundError
```

Installed `psycopg[binary]` into `/opt/novaic/services/novaic-cortex/.venv`.

Final import check:

```text
cortex_venv_psycopg=ok:3.3.4
```

## Migration Mechanics

Prepared local migration script:

```text
novaic-cortex/scripts/migrate_cortex_operational_sqlite_to_postgres.py
```

Script behavior:

- reads `/opt/novaic/data/cortex/operational.sqlite3`;
- reads `/opt/novaic/postgres/secrets/novaic_cortex_dsn`;
- creates all five operational tables in `novaic_cortex`;
- supports `--dry-run` and `--replace`;
- prints table counts only, not row contents or secrets;
- fails if source and target row counts differ.

## P036 Ready Steps

1. Back up `/opt/novaic/data/cortex/operational.sqlite3`.
2. Deploy Cortex code changes and migration script.
3. Run the migration script with `--replace`.
4. Update Cortex startup flags to include:
   - `--operational-store-backend postgres`
   - `--operational-postgres-dsn-file /opt/novaic/postgres/secrets/novaic_cortex_dsn`
5. Restart `novaic`.
6. Verify Cortex health/readiness, operational read smoke, Postgres row counts, and no active SQLite writes.

## No-Cutover Statement

Cortex remains on its current SQLite operational runtime at the end of P035. P036 is the production cutover.
