# Queue Service Confirmed-Target Startup Ticket

## Problem Definition

P115 must start Queue Service in Postgres mode against a confirmed non-production Queue Postgres target and verify health/readiness. P110/R103 currently records that no such target is available in this runner.

## Proposed Solution

1. Re-check target prerequisite before startup:
   - `NOVAIC_QUEUE_DB_BACKEND=postgres`;
   - `NOVAIC_QUEUE_POSTGRES_DSN_FILE` or `NOVAIC_QUEUE_POSTGRES_DSN`;
   - explicit non-production confirmation.
2. If the prerequisite is absent, record a startup blocker and do not start Queue Service.
3. If present, start Queue Service with explicit Postgres backend and redacted credential handling.
4. Verify startup evidence and health/readiness endpoints.

## Acceptance Criteria

- Queue Service is started only with a confirmed non-production Postgres target.
- Startup evidence proves Postgres mode.
- Health/readiness endpoints pass if the service starts.
- If the target is missing, the result records an exact blocker and no service/database mutation occurs.

## Verification Plan

- Check env var set/unset status without printing secrets.
- Verify target identity before running service startup.
- Start service only after the target gate passes.
- Record summarized health/readiness outputs with secrets redacted.

## Risks

- Starting with an ambiguous DSN could touch production; fail closed.
- Current environment likely remains blocked because P110 found no DSN/DSN file.

## Assumptions

- P114 has already cleaned the stale SQLite startup default, so remaining startup work is environment-gated.
