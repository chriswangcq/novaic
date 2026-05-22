# Queue API Staging Target And Smoke Closure Ticket

## Problem Definition

P109 must close the P106 gap by first confirming a safe non-production Queue Postgres target, then running Queue Service API smokes against the real service runtime. Current evidence says the local shell has no Queue Postgres DSN/DSN file and Docker is unavailable, so target confirmation is a separate prerequisite from smoke execution.

## Proposed Solution

1. Split the work into explicit closure units:
   - confirm or provision a non-production Queue Postgres DSN/DSN file;
   - prepare and start Queue Service in Postgres mode;
   - run health/readiness and representative API smokes;
   - record post-smoke DB counts and redacted config identity.
2. Enforce a fail-closed gate before any write:
   - no production-looking host/database/user;
   - no raw DSN in artifacts;
   - no SQLite fallback for smoke runtime.
3. Use the running service as the acceptance surface, while using existing repository tests/helpers only as implementation references.
4. If the target remains unavailable, record an explicit blocker at the target-confirmation child instead of pretending smoke validation happened.

## Acceptance Criteria

- Target confirmation and API smoke execution are tracked as separate child outcomes.
- A confirmed non-production Queue Postgres target exists before any service startup/write.
- Queue Service startup evidence proves Postgres mode.
- Health/readiness, task, saga, session, and idempotency smokes pass or produce explicit failure evidence.
- Post-smoke DB counts and redacted target public info are recorded.
- Any remaining blocker is attached to the smallest child that cannot proceed.

## Verification Plan

- Re-check required environment variables using set/unset status only.
- Validate DSN file presence and target identity without printing secrets.
- Start Queue Service with explicit `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Exercise real HTTP/API endpoints or a documented local smoke harness that talks to the running service.
- Query counts through the existing Postgres database boundary after smokes.

## Risks

- Missing staging credentials will block the first child.
- A broad one-shot execution would hide whether the blocker is target setup, service startup, or a specific API path.
- `main_novaic.py` still exposes a SQLite CLI default, so smoke commands must pin Postgres explicitly until that residue is cleaned.

## Assumptions

- The target DSN should come from `NOVAIC_QUEUE_POSTGRES_DSN_FILE` when possible.
- The current API machine or test environment can supply the non-production target outside this local shell.
- No production Queue database may be used for smoke validation.
