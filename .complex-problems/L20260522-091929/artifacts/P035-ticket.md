# Cortex Production Cutover Preflight

## Problem Definition

Cortex production cutover should not start until source SQLite counts, target `novaic_cortex` connectivity, DSN file format, dependency readiness, and current runtime health are verified.

## Proposed Solution

1. Capture current Cortex process args and readiness.
2. Capture source SQLite row counts for all five operational tables.
3. Prepare a Cortex Postgres DSN file using psycopg key/value format.
4. Verify target `novaic_cortex` connectivity and current table state.
5. Verify or install `psycopg` in the Cortex remote venv.
6. Confirm migration script is ready and no runtime switch occurs.

## Acceptance Criteria

- Cortex current readiness is ok.
- Source row counts are captured.
- Target DB is reachable without printing credentials.
- DSN file exists with mode `600`.
- Remote Cortex venv can import `psycopg`.
- Cortex remains on SQLite.

## Verification Plan

- Use redacted process inspection.
- Use SQLite count queries.
- Use psycopg connection test from the Cortex venv.
- Re-check `/ready` after dependency/DSN preparation.

## Risks

- Password special characters can break URL-style DSNs.
- Remote venv dependency management may have the same pip issue found in Gateway.
- Preflight must not restart Cortex.

## Assumptions

- Any target table data discovered during preflight must be reconciled before execution.
