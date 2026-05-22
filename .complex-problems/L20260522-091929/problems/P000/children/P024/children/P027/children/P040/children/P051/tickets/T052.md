# Validate Entangled Postgres Mode With REST Smokes

## Problem Definition

Offline migration validation is not enough. Entangled must be started in Postgres mode against a safe test target and exercised through REST endpoints to prove runtime startup, readiness, schema registration, representative reads/writes, and no active SQLite file access.

## Proposed Solution

1. Prepare a safe Postgres test target and DSN secret that is not production traffic-facing.
2. Start a staging/local Entangled process with `--db-backend postgres` and the test DSN, on a non-conflicting loopback port.
3. Verify process args and file handles show no active `/opt/novaic/data/entangled.db*` access for the staging process.
4. Register representative schemas or reuse existing app schema registration paths if available.
5. Run REST smokes for health/readiness plus representative list/read, singleton upsert/read, stream append/query, update, delete, and CAS or rowcount-sensitive behavior.
6. Capture a redacted smoke report with endpoint statuses, entity/table names, counts, and any unavailable auth/client dependency gaps.
7. Stop the staging process and leave no background test service running.

## Acceptance Criteria

- A Postgres-mode staging/local Entangled process starts successfully against a safe test target.
- `/v1/health` and `/v1/ready` return success.
- Process args/file handles prove the staging process is not opening the active SQLite database.
- Schema registration succeeds without Postgres DDL errors.
- REST smokes cover representative list/read/write/update/delete/stream/CAS behavior or document the smallest equivalent direct API proof if a route is unavailable.
- Redacted smoke report is written under ledger artifacts and contains no DSNs, tokens, cookies, or env-file contents.
- The test process is stopped or otherwise confirmed not left running.

## Verification Plan

Run the staging process, execute REST smokes, capture process/file-handle checks, inspect logs for DB/schema errors, write the report, and run full relevant local tests if code changes are required.

## Risks

- Real auth/service-token requirements may block REST calls; if so, record the exact smallest blocker and create a narrow follow-up.
- Running against the wrong target could mutate production-like data; use a dedicated staging database/port and redacted DSN file.
- Leaving a staging process running could confuse later cutover checks; cleanup must be explicit.

## Assumptions

- `P049` and `P050` have produced the migration command and fixture-backed semantic validation.
- Real WebSocket sync validation remains separate under `P052`.
