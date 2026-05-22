# Fix Queue Staging DSN And Restart Service Ticket

## Problem Definition

The staging Queue Service process on `api.gradievo.com` reaches Queue Service initialization but cannot connect to Postgres because `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` is not safe for libpq URI parsing when the generated password contains reserved URL characters.

## Proposed Solution

1. Read the existing staging Postgres environment file on the api host without printing secret values.
2. Regenerate `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` using URL-encoded credentials and the loopback endpoint `127.0.0.1:15432`.
3. Keep the DSN file at mode `0600` and owner `root`.
4. Confirm the `novaic-queue-staging-postgres` Docker container is healthy.
5. Restart the loopback-only staging Queue Service on `127.0.0.1:19987` using the DSN file.
6. Verify `/health` and `/ready`, recording only redacted evidence.

## Acceptance Criteria

- The DSN file is regenerated without exposing the secret in logs, chat, or artifacts.
- Postgres container `novaic-queue-staging-postgres` remains healthy.
- Queue Service starts with Postgres backend using the DSN file.
- `/health` passes on the staging loopback port and reports Postgres.
- `/ready` passes on the staging loopback port.
- Production service config and public ports remain untouched.

## Verification Plan

- Use a remote Python snippet to load `postgres.env`, URL-encode credentials, and rewrite the DSN file without printing it.
- Use `docker inspect` and `pg_isready` for container health.
- Restart Queue Service with the clean staging checkout and sibling `novaic-common` `PYTHONPATH`.
- Query `/health` and `/ready` locally on api host, redacting any DSN-like values in output.

## Risks

- The existing process may need to be killed by pidfile or port if it is stuck in retry.
- Health endpoints may require the service to finish schema initialization before becoming reachable.

## Assumptions

- The staging DSN should target the host loopback bind `127.0.0.1:15432`, not the container DNS name, because Queue Service is running as a host process for this smoke.
