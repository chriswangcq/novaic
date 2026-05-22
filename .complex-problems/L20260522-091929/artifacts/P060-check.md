# P060 Success Check

## Summary

`P060` is successful against `R053`. The Postgres-mode WebSocket staging runtime is prepared, reachable, ready, backed by staging Postgres fixtures, and intentionally left running for downstream WebSocket client/smoke children.

## Evidence

- `R053` confirms Entangled started on `api.gradievo.com:19910` with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.
- The redacted runtime report shows secret files at mode `600`, no raw DSN/token in the report, and process args using file flags rather than raw secret flags.
- Health and readiness returned HTTP 200 with `rest-smoke-events` and `ws-smoke-stream-events`.
- Schema registration returned HTTP 200 with 2 registered entities.
- The staging Postgres target has fixture counts: `rest_smoke_events=1`, `ws_smoke_stream_events=2`, `subagent_state_transitions=1`, and `entangled_sync_versions=1`.
- `ws_smoke_stream_events` has `entangled_rowid` with fixture range `1..2`.
- `/v1/sync` accepted a header-JWT WebSocket connection and returned a first `push` frame.
- SQLite file-handle evidence is empty.
- A follow-up sanity check confirmed port `19910` is listening, the staging PID is alive, and the staging log has zero `/v1/sync?token=` entries after remediation.

## Criteria Map

- Staging target and secret-file permissions confirmed without printing secrets: satisfied by `R053`.
- Representative schema/data present: satisfied by registered entities and fixture counts.
- Entangled starts in Postgres mode on loopback staging port: satisfied by runtime report.
- Health/readiness success: satisfied by HTTP 200 health/ready evidence.
- `/v1/sync` reachability: satisfied by header-JWT WebSocket connection.
- Process args expose file paths, not raw secrets: satisfied by secret-policy evidence.
- No active SQLite usage: satisfied by empty file-handle evidence.
- Redacted report written: satisfied by `entangled-ws-staging-runtime-report.json`.

## Execution Map

- Preflight and residue cleanup: port/process check, fixture table reset, secret-file permission check.
- Runtime startup: Entangled launched on `127.0.0.1:19910` in Postgres mode.
- Runtime preparation: schema registration plus two stream fixture appends.
- Verification: health/ready, WebSocket reachability, Postgres counts, `entangled_rowid`, SQLite file handles, and staging-log secret check.

## Stress Test

- A realistic auth/logging failure was encountered: query-string token auth caused a staging token to appear in the staging log. The run stopped the staging process, rotated the staging token, truncated the staging log, and retried with Authorization-header JWT auth. The final report confirms no remaining `/v1/sync?token=` log entries.

## Residual Risk

- This check does not claim full WebSocket protocol correctness; `P061` and `P062` still own client construction and full sync smoke validation.
- The staging process remains running intentionally for downstream WebSocket work and must be stopped by the later smoke/cleanup step if the chain pauses.

## Result IDs

- `R053`
