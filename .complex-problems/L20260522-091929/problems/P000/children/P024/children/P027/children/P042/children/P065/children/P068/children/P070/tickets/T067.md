# Deploy Repaired Entangled Runtime And Restore Production Readiness

## Problem Definition

The local Entangled Postgres placeholder fix is validated, but production Entangled on `api.gradievo.com` is still running a PG-mode process that failed schema registration and returns readiness HTTP 503 with zero entities. The repaired adapter must be deployed and production readiness restored without unfreezing Business writers.

## Proposed Solution

Copy the patched Entangled `database.py` to `/opt/novaic/services/Entangled/packages/server-python/entangled/sql/database.py` on the API host. Restart the current Entangled process on `127.0.0.1:19900` using the existing production venv, `PYTHONPATH`, `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.

After restart, push Business schemas directly to Entangled using the service token file. Build Device schema specs from the deployed Device code but post them directly to Entangled, bypassing the frozen Business proxy. Verify health/readiness, entity count/names, listener state, sanitized process args, absence of SQLite holders, Business freeze, and logs.

## Acceptance Criteria

- Patched `database.py` is deployed to the API host.
- Current broken PG-mode Entangled process is replaced by a restarted PG-mode process on `127.0.0.1:19900`.
- Restart uses file-backed DSN and service-token arguments.
- Business schemas register successfully against Entangled.
- Device schemas register successfully against Entangled without starting Business API/subscriber.
- Business API/subscriber remain stopped/frozen.
- `/v1/health` and `/v1/ready` return HTTP 200.
- Registered entity count/names are recorded and match the expected production schema set.
- No process holds `/opt/novaic/data/entangled.db*`.
- Process args contain no raw DSN or raw service-token values.
- A redacted production readiness repair report is recorded.

## Verification Plan

Use `rsync`/checksum-style inspection for deployment, sanitized `pgrep`/`ss` for runtime state, direct HTTP checks for health/readiness, schema push scripts that read secrets from files without printing them, `lsof` for SQLite holders, and log tail checks for registration errors. Record only redacted paths and counts in artifacts.

## Risks

- If schema push still fails, production Entangled remains not ready and Business writers must stay frozen.
- Device schema push must not depend on Business API because it is intentionally stopped.
- Process inspection and ad hoc scripts must not print secret file contents.

## Assumptions

- P069 has already validated the local adapter fix.
- The production DSN file and production service-token file exist under `/opt/novaic/postgres/secrets`.
- The production venv at `/opt/novaic/services/novaic-gateway/.venv/bin/python` has the required Entangled runtime dependencies.
- Business API/subscriber will be restarted by a later cutover smoke/restart step, not by P070.
