# Run Entangled Production Postgres REST And WebSocket Smokes Check

## Summary

P066 is successful. Result `R065` proves representative REST and WebSocket behavior against production Postgres-mode Entangled, including a bounded write/update/delete smoke with cleanup and a WebSocket schema/snapshot/delta/reconnect flow.

## Evidence

- REST health/readiness returned HTTP 200 with 22 entities and no missing schemas.
- REST `models` list/count checks passed.
- REST create/update/delete on a unique `models` smoke row returned HTTP 200.
- GET after delete returned HTTP 404 for the smoke row.
- `models` count was 408 before and 408 after the smoke.
- WebSocket observed schema push, snapshot, three deltas, reconnect schema, and reconnect sync.
- Smoke report secret policy says no raw token, JWT, or DSN was recorded and no query-string token was used.
- Production log error tail in the smoke report is empty.

## Criteria Map

- Representative REST read smoke passes: satisfied by health/readiness/list/count checks.
- Bounded REST write/update/delete passes without corrupting production data: satisfied by unique `models` smoke row create/update/delete, 404 after delete, and unchanged count.
- WebSocket schema/list/stream/delta/reconnect smoke passes: satisfied by schema, snapshot, insert/update/delete deltas, and reconnect `up_to_date`.
- Postgres counts/key values remain sane: satisfied by `models` count 408 before and after and readiness remaining 22 entities.
- Reports/log checks confirm no raw secrets: satisfied by smoke report secret policy and empty log error tail.
- Smoke-created rows cleaned up: satisfied by delete 200 and get-after-delete 404.

## Execution Map

- T068 executed a one-go production smoke suite.
- R065 recorded REST, WebSocket, cleanup, count, and secret-policy evidence.
- No runtime child problem was needed.

## Stress Test

- The smoke touched both synchronous REST CRUD and live WebSocket notification paths.
- The write smoke used a unique `codex-smoke-model-*` primary key and verified count equality after cleanup.
- Reconnect used the latest observed version and returned `up_to_date`, exercising version continuity after deltas.

## Residual Risk

- Business API/subscriber are still intentionally frozen and must be restarted/verified in the next cutover step.
- SQLite residue removal remains assigned to P067.

## Result IDs

- R065
