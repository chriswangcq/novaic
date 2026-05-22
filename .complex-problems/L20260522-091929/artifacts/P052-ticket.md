# Validate Entangled Postgres WebSocket Sync Path

## Problem Definition

Entangled's REST staging path has passed, but the WebSocket `/v1/sync` path still needs a dedicated Postgres-mode smoke before production cutover. The test must prove that schema frames, full/head sync state, persisted sync versions, write deltas, reconnect behavior, and stream ordering remain correct when the backing store is Postgres instead of SQLite.

## Proposed Solution

Start a safe Postgres-mode Entangled staging process on the API machine using the existing staging DSN/token secret files, then run or build a small WebSocket smoke client against `/v1/sync`. Use representative fixture entities already available from REST staging where possible, and add the smallest additional fixture schema/data needed to observe stream/list/form behavior. Capture a redacted report with endpoint, entity names, frame types, version observations, row counts, stream ordering checks, and cleanup status. Stop the staging process after the smoke.

## Acceptance Criteria

- A documented WebSocket smoke command or script connects to a Postgres-mode staging/test `/v1/sync` endpoint.
- The smoke records schema/full/head sync behavior or the closest protocol frames available from the current server.
- The smoke performs or observes a write and verifies a delta/push path without decreasing or resetting persisted sync versions.
- A controlled disconnect/reconnect or restart/reconnect check proves persisted versions remain safe.
- Stream ordering is checked for no duplicate or skipped rows where `entangled_rowid` participates.
- The final report redacts tokens, cookies, DSNs, passwords, and payload secrets.
- The staging process is stopped or its continued lifetime is explicitly justified for the next step.

## Verification Plan

Run local unit tests for any client/helper code, then execute the smoke against the remote staging process. Verify the redacted report and, if useful, query the staging Postgres target through the `novaic-postgres` container to confirm sync-version monotonicity and stream row/order expectations without exposing secrets.

## Risks

- The current WebSocket protocol may require client behavior that is not obvious from REST tests.
- Remote Python environment issues may require using a local client against the SSH-exposed loopback endpoint or installing a small dependency.
- If the real production WebSocket client context is unavailable, the smoke may need to document the closest direct protocol proof and create one narrow follow-up.

## Assumptions

- The staging Postgres DB/role/DSN/token files created for REST staging can be reused safely for WebSocket staging.
- Fixture data is sufficient for this validation if it exercises representative schema/full/head/delta/stream behavior.
- Production Entangled remains untouched until a later cutover problem explicitly owns that change.
