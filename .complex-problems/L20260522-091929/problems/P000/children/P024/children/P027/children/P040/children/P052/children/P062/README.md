# Run Entangled Postgres WebSocket Sync Smoke

## Problem

After a Postgres-mode staging runtime and smoke client exist, the actual WebSocket sync behavior must be proven and reported. Run the smoke against the staging `/v1/sync` endpoint, verify schema/full/head behavior, write/delta propagation, reconnect safety, persisted sync-version monotonicity, and stream ordering with `entangled_rowid`. This belongs under `P052` because it closes the high-risk runtime sync path before production cutover.

## Success Criteria

- The smoke connects to the Postgres-mode staging `/v1/sync` endpoint and records endpoint, entity names, frame types, and counts.
- Schema/full/head sync behavior is verified for representative form/list/stream entities or the closest available protocol frames are documented.
- A write is performed or observed and a delta/push path is verified without decreasing or resetting persisted sync versions.
- A controlled disconnect/reconnect or restart/reconnect check proves persisted versions remain safe.
- Stream ordering checks show no duplicate or skipped rows where `entangled_rowid` participates.
- The redacted report contains no tokens, cookies, DSNs, passwords, or payload secrets.
- The staging process is stopped after validation or its continued lifetime is explicitly justified.
