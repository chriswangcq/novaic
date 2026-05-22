# Prepare WebSocket Postgres Staging Runtime

## Problem Definition

`P060` needs a safe Postgres-mode Entangled runtime that can be used by the later WebSocket smoke client. The runtime must use the existing staging database and secret files, expose `/v1/sync` only on a safe loopback staging port, have representative sync fixtures ready, and prove it is not using the active SQLite database.

## Proposed Solution

Reuse the dedicated `novaic_entangled_rest_staging` database and secret files created during REST staging. Confirm or reset the staging target to a safe fixture state, add any minimal schema/data needed for WebSocket form/list/stream checks, start Entangled on a loopback staging port in Postgres mode with `--service-token-file`, verify health/readiness and `/v1/sync` reachability, check for active SQLite file handles, and write a redacted runtime/setup report. Leave the process running only if the next child needs it immediately; otherwise stop it and document that.

## Acceptance Criteria

- Staging Postgres target and secret-file permissions are confirmed without printing secret values.
- Representative schema/data needed by WebSocket sync validation is present in the staging target.
- Entangled starts with `--db-backend postgres` on a loopback staging port.
- Health/readiness return success.
- `/v1/sync` is reachable enough to distinguish endpoint availability from client protocol validation.
- Process arguments expose secret-file paths, not raw DSN/token values.
- File-handle checks show no active SQLite database usage.
- A redacted setup/runtime report is written.

## Verification Plan

Use remote shell checks over SSH, Postgres queries through `docker exec novaic-postgres psql`, local or remote curl/probe commands for health/readiness and `/v1/sync`, and `lsof`/`ss`/process inspection for port and file-handle verification. Store only redacted status/counts in the artifact report.

## Risks

- The previous REST staging process was stopped, so stale process/port state must be verified before starting.
- The WebSocket endpoint may reject a raw HTTP probe even while healthy; the ticket only needs reachability/protocol boundary evidence, not full protocol success.
- Reusing the REST staging target is safe only if it remains isolated from production Entangled data.

## Assumptions

- The API host still has the Postgres-capable Entangled package synced from REST staging.
- The staging DB/role/DSN/token files under `/opt/novaic/postgres/secrets` remain available.
- Later child problems own the actual WebSocket client behavior and full smoke execution.
