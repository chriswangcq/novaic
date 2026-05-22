# Cortex Production Cutover Preflight

## Problem

Before switching production Cortex to Postgres, remote runtime, source counts, target DB readiness, DSN file, dependency readiness, and migration mechanics must be verified without restart/backend switch.

## Success Criteria

- Current Cortex runtime and readiness are captured.
- Source SQLite row counts for all five operational tables are captured.
- `novaic_cortex` target DB is reachable and target table state is known.
- DSN file exists with restrictive permissions and is connection-tested without printing credentials.
- Remote Cortex venv can import `psycopg`.
- Migration script is ready for execution.
- Cortex remains on SQLite during preflight.
