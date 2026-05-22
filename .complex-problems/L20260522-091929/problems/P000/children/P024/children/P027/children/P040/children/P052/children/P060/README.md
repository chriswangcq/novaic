# Prepare Entangled Postgres WebSocket Staging Runtime

## Problem

The WebSocket smoke needs a safe Entangled process running in Postgres mode with representative schema/data available for sync validation. Prepare or reuse the dedicated staging Postgres target, start a loopback staging runtime with file-based secrets, ensure the `/v1/sync` endpoint can be reached, and verify the runtime is not opening the active SQLite database file. This belongs under `P052` because WebSocket protocol checks are only meaningful against a running Postgres-mode service.

## Success Criteria

- A dedicated staging/test Postgres target is confirmed ready for WebSocket sync validation.
- Any needed representative form/list/stream schema or fixture data is registered or imported without touching production Entangled data.
- Entangled starts in Postgres mode on a safe loopback staging port using DSN/token secret files rather than raw process-argument secrets.
- Health/readiness and basic `/v1/sync` reachability are verified.
- File-handle checks show no active SQLite database usage by the staging runtime.
- A redacted setup/runtime report is captured, and the process lifetime is explicitly stated for downstream smoke execution.
