# Gateway Production Cutover Preflight

## Problem Definition

Gateway production cutover should not begin until remote runtime, source/target data state, dependency readiness, DSN file handling, and migration mechanics are verified.

## Proposed Solution

1. Capture current Gateway process, health, and source SQLite row counts.
2. Verify `novaic_gateway` database can be reached from the `api` host without printing credentials.
3. Prepare or verify a root-readable Gateway DSN file for the existing Postgres service.
4. Verify or install the remote Gateway `psycopg` dependency without restarting Gateway.
5. Prepare a migration command/script path for P032.
6. Record all evidence and stop before runtime backend switch.

## Acceptance Criteria

- Gateway current health and runtime mode are known.
- Source row counts are captured for `users`, `refresh_tokens`, and `config`.
- Target Postgres DB is reachable and current table state is known.
- DSN file exists with restrictive permissions or a specific creation step is ready.
- Remote Gateway venv can import `psycopg`.
- Migration mechanics are prepared for P032.
- Gateway remains on SQLite during preflight.

## Verification Plan

- Use remote commands that redact secrets.
- Use SQLite count queries against `/opt/novaic/data/gateway.db`.
- Use `psql`/container exec to verify target DB connectivity and table state.
- Use Python import check in the remote Gateway venv.
- Re-check Gateway `/api/health` at the end.

## Risks

- Accidental secret output in logs.
- Installing a dependency into the active venv can change files, though it should not affect the running process until restart.
- Existing target tables could contain stale partial data and must be handled before execution.

## Assumptions

- No production restart/backend switch happens in this preflight.
- If target Postgres already contains data, P032 must choose truncate/reload or reconciliation explicitly.
