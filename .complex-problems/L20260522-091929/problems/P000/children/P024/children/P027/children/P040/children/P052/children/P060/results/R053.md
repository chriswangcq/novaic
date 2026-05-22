# Entangled WebSocket Postgres Staging Runtime Result

## Summary

`T057` prepared a safe Entangled Postgres-mode WebSocket staging runtime on `api.gradievo.com:19910`. The runtime uses staging DB/token files, registered representative REST/list and WebSocket stream smoke entities, inserted two stream fixture rows, verified health/readiness, confirmed `/v1/sync` reachability with a header-based JWT, and found no active SQLite file handles. The staging process is intentionally left running for the next WebSocket client/smoke children.

## Done

- Confirmed no prior listener or staging process was using port `19910`.
- Confirmed staging DSN and token secret files exist with `0600` permissions.
- Cleaned prior `ws_smoke_stream_events` fixture residue from the dedicated staging Postgres database.
- Started Entangled in Postgres mode on loopback port `19910` using `--postgres-dsn-file` and `--service-token-file`.
- Registered two smoke entities:
  - `rest-smoke-events`
  - `ws-smoke-stream-events`
- Inserted two `ws-smoke-stream-events` fixture rows for later stream-order validation.
- Verified `/v1/health` and `/v1/ready` returned HTTP 200 with both entities ready.
- Verified a `/v1/sync` WebSocket handshake succeeds using a JWT in the Authorization header.
- Verified `ws_smoke_stream_events` has `entangled_rowid` and fixture rowids span `1..2`.
- Verified no active SQLite file handles for the staging process.
- Wrote a redacted runtime report.

## Verification

- Remote health: HTTP 200, status `ok`, entities `rest-smoke-events` and `ws-smoke-stream-events`.
- Remote readiness: HTTP 200, status `ready`, no missing entities.
- Schema registration: HTTP 200, total 2 registered entities.
- Fixture inserts: two POST `/append` calls returned HTTP 200.
- Staging Postgres counts:
  - `entangled_sync_versions`: 1
  - `rest_smoke_events`: 1
  - `ws_smoke_stream_events`: 2
  - `subagent_state_transitions`: 1
- `/v1/sync` reachability: connected successfully; first observed frame type was `push`.
- Secret policy:
  - report records no raw DSN or raw token.
  - process args use secret-file flags, not raw DSN/token flags.
  - staging log has no `/v1/sync?token=` entries after remediation.

## Known Gaps

- This ticket only prepares the runtime and fixture surface. `P061` owns a reproducible WebSocket smoke client, and `P062` owns full schema/full/head/delta/reconnect/stream-order validation.
- During execution, an initial probe attempted query-string token auth and caused the staging log to contain the staging token. That was remediated by stopping staging, rotating the staging token file, truncating the staging log, and retrying with Authorization-header JWT auth. No production token was involved.
- The staging process is left running for the next WebSocket children and must be stopped by `P062` or by manual cleanup if the chain is paused.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-ws-staging-runtime-report.json`
- `/opt/novaic/logs/entangled-ws-staging.log`
- `/opt/novaic/entangled-ws-staging.pid`
