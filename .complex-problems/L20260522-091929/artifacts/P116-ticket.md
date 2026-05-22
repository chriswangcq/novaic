# Start Queue Service After DSN Ticket

## Problem Definition

P116 is the explicit unblock point for Queue Service startup. Code cleanup is complete, but the runner still needs a confirmed non-production Queue Postgres DSN/DSN file before starting the service and checking health/readiness.

## Proposed Solution

1. Wait for or receive a confirmed non-production Queue Postgres target via:
   - `NOVAIC_QUEUE_POSTGRES_DSN_FILE`, preferred; or
   - `NOVAIC_QUEUE_POSTGRES_DSN`, direct fallback.
2. Verify the target identity is staging/test/non-production without printing secrets.
3. Start Queue Service with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
4. Verify startup evidence and health/readiness.
5. Record redacted startup evidence and any failure output.

## Acceptance Criteria

- The DSN/DSN file prerequisite is explicit and redacted.
- Queue Service starts only after the target is confirmed non-production.
- Startup evidence proves Postgres mode.
- Health/readiness endpoints pass.
- Failure to supply a target remains a clear external blocker rather than a service failure.

## Verification Plan

- Check env var set/unset status first.
- Confirm DSN file path existence if using file-based credentials.
- Start service only after non-production confirmation.
- Call health/readiness endpoints and summarize responses.

## Risks

- This ticket cannot complete in the current runner until a staging DSN is supplied.
- Direct DSN usage risks shell history leakage; DSN file is safer.

## Assumptions

- The user or deployment environment will provide the staging DSN/DSN file.
- P114's Postgres default cleanup remains in place.
