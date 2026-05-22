# Queue Service API Smoke Ticket

## Problem Definition

Queue Service is now running in Postgres mode on `api.gradievo.com` with a dedicated staging DSN. `P112` must exercise representative HTTP APIs against the real service runtime and record redacted evidence without using SQLite fallback.

## Proposed Solution

1. Run a remote smoke script on `api.gradievo.com` against `http://127.0.0.1:19987`.
2. Obtain the internal queue API key from runtime config inside the remote process without printing it.
3. Exercise:
   - `/health` and `/ready`;
   - task publish, claim, complete, fail;
   - saga create, claim, launched, complete, fail;
   - session dispatch, session-ended, sessions, pending diagnostics;
   - task idempotency acquire, duplicate in-progress acquire, complete, completed-result acquire.
4. Query post-smoke row counts from the staging Postgres container.
5. Store a redacted JSON smoke report under the ledger artifacts directory.

## Acceptance Criteria

- Health/readiness smoke passes.
- Task publish/claim/complete/fail smoke passes.
- Saga create/claim/launch/complete/fail smoke passes, or skipped steps have explicit safety/environment reasons.
- Session dispatch/finalize/rebuild or safe equivalent passes, or skipped steps have explicit reasons.
- Idempotency duplicate/in-progress/completed-result smoke passes.
- No raw DSN or internal key is printed or written to artifacts.

## Verification Plan

- Execute the remote Python smoke script with `requests`.
- Fail the script on unexpected HTTP status or unexpected response shape.
- Write a compact JSON report containing operation names, public ids/statuses, counts, and any explicit skips.
- Confirm post-smoke DB counts through `psql` inside `novaic-queue-staging-postgres`.

## Risks

- Some session finalize behavior may require worker-side saga creation; use the safest route-level equivalent if no live worker exists.
- Saga lifecycle may require separate saga instances for complete and fail paths.
- Internal key must be used but never shown.

## Assumptions

- The running staging process from `P111` remains available on `127.0.0.1:19987`.
- Writing test rows into the dedicated staging Postgres database is safe.
