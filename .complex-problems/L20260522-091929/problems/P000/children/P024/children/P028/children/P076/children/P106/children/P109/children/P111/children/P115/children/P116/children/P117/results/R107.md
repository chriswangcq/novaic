# Queue Staging DSN Supply Result

## Summary

Provisioned an independent non-production Queue Postgres target on `api.gradievo.com` for staging validation. The target is a dedicated Docker container with a dedicated database, user, volume, and DSN file. No DSN secret value was printed into this artifact.

## Done

- Connected to `api.gradievo.com` as `root` and confirmed Docker is available.
- Observed an existing `novaic-postgres` container but did not reuse it for Queue staging.
- Created or reused a separate staging-only Postgres container:
  - container: `novaic-queue-staging-postgres`
  - image: `postgres:16-alpine`
  - host bind: `127.0.0.1:15432`
  - database: `novaic_queue_staging`
  - user: `novaic_queue_staging`
  - volume: `novaic_queue_staging_pgdata`
  - restart policy: `unless-stopped`
- Created secret files on the remote host with `0600` permissions:
  - env file: `/opt/novaic/queue-staging-postgres/postgres.env`
  - DSN file: `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`
- Confirmed the container health status is `healthy`.
- Confirmed `pg_isready` passes inside the container.

## Verification

- `docker --version` succeeded on `api.gradievo.com`.
- `docker ps` showed existing production-ish/shared services; Queue staging uses a separate container and volume.
- Final setup output:
  - `container=novaic-queue-staging-postgres`
  - `status=healthy`
  - `host_bind=127.0.0.1:15432`
  - `database=novaic_queue_staging`
  - `user=novaic_queue_staging`
  - `dsn_file=/opt/novaic/queue-staging-postgres/queue-postgres.dsn`
  - `env_file=/opt/novaic/queue-staging-postgres/postgres.env`
  - `volume=novaic_queue_staging_pgdata`

## Known Gaps

- This closes the target-supply prerequisite only. Queue Service has not yet been started against this DSN in the P117 ticket.
- The DSN file is on the remote `api.gradievo.com` host. Follow-up startup/smoke execution should either run on that host or establish a safe tunnel and local DSN file without printing the secret.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/P117-T112-result.md`
