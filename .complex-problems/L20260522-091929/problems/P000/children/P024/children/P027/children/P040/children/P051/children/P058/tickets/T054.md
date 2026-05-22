# Start Entangled In Postgres Mode For REST Staging

## Problem Definition

With a safe staging Postgres target available, start a non-production Entangled process in Postgres mode on a loopback staging port and prove readiness without opening the active SQLite database.

## Proposed Solution

1. Inspect the API host Entangled runtime layout and confirm whether the deployed package supports `--db-backend postgres`.
2. If needed, deploy only the Entangled package changes required for a staging process, without changing the production Entangled process.
3. Start a staging process with `--db-backend postgres`, `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_rest_staging_dsn`, and a non-conflicting loopback port.
4. Verify `/v1/health` and `/v1/ready`.
5. Inspect process args with secrets redacted and verify file handles do not include active SQLite database paths.
6. Inspect logs for Postgres DDL/readiness errors.
7. Stop the staging process after validation unless the next REST smoke ticket explicitly needs it running.

## Acceptance Criteria

- A staging Entangled process starts in Postgres mode on a non-production port.
- Health/readiness succeed.
- Process args show Postgres mode and DSN-file usage without raw secrets.
- File-handle checks show no active SQLite DB files opened by the staging process.
- Startup logs show no Postgres schema/readiness failures.
- Lifecycle report records PID/port/log path and whether the process was stopped or intentionally left for the next child.

## Verification Plan

Run remote inspection/start commands through SSH, collect redacted process/health/lsof/log evidence, and write a ledger report. Do not modify the production process.

## Risks

- Remote runtime may not yet include local Postgres Entangled code; if so, record a blocker or deploy a staging-only copy.
- Starting the service with the wrong DSN or port could interfere with production; use the staging DSN file and loopback-only port.
- Service token requirements may affect readiness or later REST smokes; do not print tokens.

## Assumptions

- `P057` staging target and DSN file exist.
- REST endpoint mutation tests are handled by the next child.
