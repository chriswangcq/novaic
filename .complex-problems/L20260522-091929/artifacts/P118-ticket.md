# Start Queue Service On Api Ticket

## Problem Definition

Queue staging Postgres is available on `api.gradievo.com`, but Queue Service has not yet been started against it. P118 must start the real service runtime on the api host using the staging DSN file and verify health/readiness.

## Proposed Solution

1. Inspect the api host for an existing `new-build-novaic` checkout or service layout.
2. Use the current merged `main` code for `novaic-agent-runtime`.
3. Start Queue Service on a non-public loopback port with:
   - `NOVAIC_QUEUE_DB_BACKEND=postgres`
   - `NOVAIC_QUEUE_POSTGRES_DSN_FILE=/opt/novaic/queue-staging-postgres/queue-postgres.dsn`
4. Prefer a disposable smoke process or dedicated staging container; do not alter production service config.
5. Verify health/readiness endpoints and record redacted startup evidence.

## Acceptance Criteria

- Queue Service starts on `api.gradievo.com` with Postgres backend.
- The DSN source is the staging DSN file, not a direct printed secret.
- Health/readiness endpoint passes.
- Startup artifacts/log summaries do not expose DSN secrets.
- Production Queue/Gateway services are not reconfigured by this ticket.

## Verification Plan

- Confirm remote checkout or clone/pull `novaic-agent-runtime` main.
- Start service on a loopback staging port.
- Query health/readiness locally from the api host.
- Stop disposable process if it is only needed for smoke, unless a dedicated staging service is intentionally left running.

## Risks

- Python dependencies may be missing on the api host.
- Existing production ports must not be reused.
- If service import/startup expects local monorepo paths, startup may require environment setup before the smoke can run.

## Assumptions

- Running a loopback-only staging Queue Service process on the api host is acceptable for validation.
- `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` is the staging DSN file created by P117.
