# Run Entangled Production Postgres REST And WebSocket Smokes Result

## Summary

Production Entangled Postgres smokes passed against `127.0.0.1:19900`. REST health/readiness/read/count checks succeeded, a bounded `models` row create/update/delete smoke succeeded and was cleaned up, and WebSocket schema/snapshot/delta/reconnect behavior was observed without recording raw secrets.

The smoke-created row `codex-smoke-model-1779451644008` was deleted and a follow-up GET returned 404. `models` count was 408 before and 408 after the smoke. WebSocket saw schema, snapshot, insert/update/delete deltas, and reconnect `up_to_date`.

## Done

- Ran REST health and readiness checks.
- Ran REST `models` count and list checks.
- Created a unique `models` smoke row.
- Updated and read back the smoke row.
- Deleted the smoke row and verified it was missing afterward.
- Connected to `/v1/sync` with Authorization-header JWT auth.
- Observed WebSocket schema push with 22 entities.
- Entangled `models` over WebSocket and observed snapshot plus insert/update/delete deltas.
- Reconnected using the latest version and observed an `up_to_date` sync frame.
- Pulled the redacted smoke report into the ledger artifacts.

## Verification

- `/v1/health` returned HTTP 200 with 22 entities.
- `/v1/ready` returned HTTP 200 with `status: ready` and `missing: []`.
- REST create/update/delete returned HTTP 200.
- GET after delete returned HTTP 404 for the smoke row.
- `models` count was 408 before and 408 after smoke cleanup.
- WebSocket observations recorded `schema_seen: true`, `snapshot_seen: true`, `delta_count: 3`, `reconnect_schema_seen: true`, and `reconnect_sync_seen: true`.
- The smoke report recorded `report_contains_secret: false`, `raw_token_recorded: false`, `raw_jwt_recorded: false`, and `raw_dsn_recorded: false`.
- Production log error tail in the smoke report was empty.

## Known Gaps

- Business API/subscriber are still intentionally frozen and need to be restarted/verified by the next cutover step.
- SQLite residue has not yet been archived/removed; that remains assigned to P067.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-production-smoke-report.json`
- `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled-production-smoke-report.json`
