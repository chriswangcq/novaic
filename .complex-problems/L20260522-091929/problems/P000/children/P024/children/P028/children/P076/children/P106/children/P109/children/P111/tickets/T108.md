# Queue Service Postgres Startup Ticket

## Problem Definition

P111 must make Queue Service startup unambiguously Postgres-mode for staging smokes. Current target confirmation (P110/R103) says no non-production DSN is available, and code inspection found a stale-looking `main_novaic.py` CLI default that still falls back to `sqlite`.

## Proposed Solution

1. Clean the startup boundary so Queue Service runtime entrypoints default to Postgres rather than SQLite.
2. Keep SQLite only as an explicit adapter/test mode, not as an accidental service default.
3. Add or update tests that guard the startup default and prevent future fallback drift.
4. If a confirmed non-production DSN is unavailable, record a startup blocker without launching the service.
5. If a DSN is later supplied, start Queue Service with `NOVAIC_QUEUE_DB_BACKEND=postgres` and record startup/health evidence.

## Acceptance Criteria

- Active Queue Service startup defaults are unambiguously Postgres.
- Any remaining SQLite mode is explicit and test-scoped, not an implicit production/runtime fallback.
- Tests guard the startup default.
- If no DSN is available, the result records a precise blocker and does not start the service.
- If a DSN is available, Queue Service starts and health/readiness pass.

## Verification Plan

- Inspect startup entrypoints for `NOVAIC_QUEUE_DB_BACKEND` defaults.
- Patch stale SQLite startup default if present.
- Run focused startup/default tests.
- Check current DSN env presence without printing secrets.
- Start the service only after a confirmed non-production DSN exists.

## Risks

- Changing defaults can affect local developer scripts that relied on implicit SQLite.
- Starting without a confirmed DSN could either fail noisily or accidentally hit the wrong target; fail closed.

## Assumptions

- The intended current server default is Postgres.
- SQLite is acceptable only when selected explicitly for unit tests or adapter-level local checks.
