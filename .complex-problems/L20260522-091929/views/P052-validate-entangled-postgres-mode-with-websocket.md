# P052: Validate Entangled Postgres Mode With WebSocket Sync Smokes

Status: done
Parent: P040
Root: P000
Source Ticket: T045 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P052
Body: problems/P000/children/P024/children/P027/children/P040/children/P052/README.md
Ticket(s): T056

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

## Subproblems
- P060: Prepare Entangled Postgres WebSocket Staging Runtime
- P061: Build Entangled WebSocket Sync Smoke Client
- P062: Run Entangled Postgres WebSocket Sync Smoke

## Results
- R056

## Latest Check
C058

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P052/README.md
- Ticket T056: problems/P000/children/P024/children/P027/children/P040/children/P052/tickets/T056.md
- Result R056: problems/P000/children/P024/children/P027/children/P040/children/P052/results/R056.md
- Check C058: problems/P000/children/P024/children/P027/children/P040/children/P052/checks/C058.md

## Follow-ups
- none
