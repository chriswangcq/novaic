# Entangled Postgres WebSocket Sync Smoke Result

## Summary

`T059` ran the final Entangled WebSocket sync smoke against the Postgres-mode staging runtime. The run prepared a non-BLOB list fixture for representative list coverage, executed the `entangled-ws-smoke` client with stream writes and Postgres evidence enabled, verified schema/list/stream/delta/reconnect behavior, confirmed sync versions did not decrease, checked stream `entangled_rowid` evidence, verified redaction, and stopped the staging process.

## Done

- Registered non-BLOB list fixture entity `ws-smoke-list-items` to isolate the known BLOB/list serialization issue from representative list sync coverage.
- Inserted two list fixture rows.
- Ran `entangled-ws-smoke` against `ws://127.0.0.1:19910/v1/sync` with:
  - Authorization-header JWT auth.
  - REST append enabled for stream delta.
  - Postgres DSN-file evidence enabled.
  - `ws-smoke-list-items` as the list entity.
  - `ws-smoke-stream-events` as the stream entity.
- Captured final redacted report at `/opt/novaic/logs/entangled-ws-smoke-final.json`.
- Stopped the staging process and verified port `19910` has no listener.

## Verification

- Final smoke observations:
  - `schema_seen`: true.
  - `list_sync_mode`: `snapshot`.
  - `stream_sync_mode`: `head_n`.
  - `delta_seen`: true.
  - `reconnect_sync_mode`: `up_to_date`.
  - `list_skipped`: false.
- Sync-version evidence:
  - Before: stream scoped/global versions were both 1.
  - After: stream scoped/global versions were both 2; list version was 2.
  - `version_non_decreasing`: true.
- Stream ordering/count evidence:
  - stream count: 4.
  - `entangled_rowid` range: 1..4.
- Secret/redaction evidence:
  - Authorization-header auth used.
  - query-string token usage: false.
  - raw DSN/JWT/token recorded: false.
  - report contains secret: false.
  - staging log `/v1/sync?token=` entries after cleanup: 0.
- Cleanup evidence:
  - `port_19910_listeners_after`: 0.
  - `staging_pid_alive_after`: false.

## Known Gaps

- The BLOB/list serialization issue discovered in `P061` was isolated by using a non-BLOB list fixture. It remains a real residual risk if production WebSocket clients subscribe to BLOB-bearing list entities.
- This ticket validates staging behavior only; production Entangled cutover remains separate.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-ws-smoke-final-summary.json`
- `/opt/novaic/logs/entangled-ws-smoke-final.json`
- `/opt/novaic/logs/entangled-ws-smoke-final-summary.json`
