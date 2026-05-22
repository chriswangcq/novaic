# Queue Service Postgres API Staging Smoke Ticket

## Problem Definition

P106 must prove the real Queue Service runtime can start in Postgres mode and exercise representative Queue APIs against a confirmed non-production staging target. P105 closed with a precise blocker: no safe staging Queue Postgres DSN/DSN file is currently available in this shell/workspace/Docker context.

## Proposed Solution

1. Re-check the P105 prerequisite before execution:
   - require `NOVAIC_QUEUE_DB_BACKEND=postgres`;
   - require either `NOVAIC_QUEUE_POSTGRES_DSN_FILE` or `NOVAIC_QUEUE_POSTGRES_DSN`;
   - require the target to be explicitly non-production by hostname/database naming or user/deployment confirmation.
2. If the prerequisite is still missing, record a blocker result without starting the service or touching any database.
3. If a safe target exists, start Queue Service in Postgres mode with secrets redacted from logs/artifacts.
4. Run representative API smokes:
   - health/readiness;
   - task publish/claim/complete/fail or safe retry equivalent;
   - saga create/claim/launch/complete/fail or safe equivalent;
   - session dispatch/finalize/rebuild or safe equivalent;
   - idempotency duplicate, in-progress, and completed-result scenarios.
5. Query and record post-smoke table counts/config identity with DSNs redacted.

## Acceptance Criteria

- The ticket either produces a full staging smoke report or a precise blocker report tied to the missing P105 prerequisite.
- No production Queue database is used or mutated.
- Service startup evidence proves Postgres mode, not SQLite fallback.
- All smoke endpoints/actions and post-smoke counts are recorded with secrets redacted.
- Any skipped smoke is explicitly justified as unsafe or impossible in the current environment.

## Verification Plan

- Inspect active environment variable names and redacted database public info before service startup.
- Use the real Queue Service process/API surface rather than repository-only unit tests when a staging target exists.
- Fail closed if the DSN identity is ambiguous or absent.
- Record command outputs as summarized evidence rather than dumping secrets or raw DSNs.

## Risks

- Accidentally using a production DSN would be unacceptable; target ambiguity must stop execution.
- The current environment likely still lacks staging credentials, so the first execution may produce a blocker instead of smoke results.
- API smoke setup may require an internal key or port selection not present in the current shell.

## Assumptions

- P105's blocker remains authoritative until a confirmed non-production DSN/DSN file is supplied.
- `NOVAIC_QUEUE_POSTGRES_DSN_FILE` is preferred over direct `NOVAIC_QUEUE_POSTGRES_DSN` for credential hygiene.
- Existing Queue Service tests and migration helpers can be used as smoke design references, but the P106 acceptance surface is the running service.
