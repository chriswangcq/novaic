# Validate Queue Postgres Mode In Staging

## Problem Definition

The Queue repositories and migration tooling are implemented, but unit tests do not prove the actual Queue Service process, workers, outbox workers, and representative APIs run correctly against a non-production Postgres target. P076 must create and execute a staging validation plan that avoids production data and records a redacted evidence report.

## Proposed Solution

1. Prepare a staging/test `novaic_queue` Postgres target:
   - use a non-production DSN;
   - initialize current Queue schema;
   - optionally run the migration tool against a sanitized SQLite fixture or copied staging queue DB.
2. Start Queue Service in Postgres mode:
   - `NOVAIC_QUEUE_DB_BACKEND=postgres`;
   - DSN via file or redacted env;
   - verify health/readiness.
3. Run representative API smokes:
   - task publish/claim/complete/fail/retry or safe equivalents;
   - saga create/claim/launch/complete/fail safe path;
   - session dispatch/finalize/rebuild smoke where available;
   - outbox drain/retry smoke;
   - idempotency duplicate/in-progress/completed-result smoke.
4. Start representative workers/outbox workers against the staging Queue Service and verify they do not create/use SQLite queue file holders.
5. Record a redacted staging report with commands, counts, health checks, DB counts, and failures.

## Acceptance Criteria

- Staging/test Queue Postgres database is prepared without production queue writes.
- Queue Service starts in Postgres mode and readiness/health endpoints pass.
- Representative task, saga, session, outbox, and idempotency smokes pass.
- Worker/outbox processes can connect to Queue Service in Postgres mode without SQLite queue file usage.
- Report redacts DSNs/secrets and captures commands, counts, statuses, and residual risks.

## Verification Plan

- Prefer an executable staging smoke script/report artifact if staging credentials are available.
- If credentials are not available in this environment, produce the smallest blocker child that records the missing dependency and exact command plan.
- Reuse P075 migration report format where useful.

## Risks

- This step may be blocked by missing non-production Postgres credentials or by lack of a safe staging runtime on the local machine.
- Do not run against production data or production Queue Service during P076.

## Assumptions

- Live production cutover remains P077; P076 is staging/non-production only.
