# Validate Entangled Postgres Mode With WebSocket Sync Smokes

## Problem

Entangled's WebSocket sync path is one of the highest-risk parts of the SQLite-to-Postgres cutover because it depends on schema frames, sync versions, stream ordering, and persisted deltas. This belongs under `P040` because production cutover should not proceed until a Postgres-mode sync smoke proves the migrated/staging target behaves like the current runtime.

## Success Criteria

- A WebSocket smoke script or documented command connects to a Postgres-mode staging/test Entangled `/v1/sync` endpoint.
- The smoke verifies schema/full/head sync behavior for representative form/list/stream entities or records the closest equivalent protocol frames available in the staging environment.
- The smoke performs or observes a write and verifies a delta/push path without decreasing or resetting persisted sync versions.
- Reconnect behavior is tested after restart or a controlled disconnect, and persisted versions remain safe.
- The smoke verifies stream ordering does not duplicate or skip rows when `entangled_rowid` is involved.
- The result report records endpoint, entity names, frame types/checks, and counts while redacting tokens, cookies, DSNs, and payload secrets.
- If the real WebSocket client context is unavailable, the result creates one narrow follow-up rather than treating an unrun smoke as success.
