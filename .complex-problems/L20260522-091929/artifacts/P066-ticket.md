# Run Entangled Production Postgres REST And WebSocket Smokes

## Problem Definition

Production Entangled is now ready in Postgres mode, but cutover confidence requires representative REST and WebSocket protocol checks before SQLite residue is archived. The smokes must be bounded, avoid leaking secrets, and clean up any test rows they create.

## Proposed Solution

Run production smokes directly against `http://127.0.0.1:19900` on the API host using the production service token file. Verify REST health/schema/read behavior, perform a bounded write/update/delete on a safe test entity using a unique smoke ID, and run the packaged WebSocket smoke client against the production WebSocket endpoint. Capture pre/post counts or entity-list sanity values, confirm logs/reports do not include raw DSN/token/JWT values, and clean up any smoke-created rows.

## Acceptance Criteria

- REST health/readiness and schema/entity read checks pass against production Postgres-mode Entangled.
- A safe REST write/update/delete smoke passes or the smoke-created row is explicitly cleaned up.
- WebSocket smoke passes for schema/list/stream/delta/reconnect behavior or records a justified equivalent.
- Post-smoke entity counts/readiness remain sane.
- No raw DSN/token/JWT values are recorded in local artifacts.
- Production logs show no new smoke-related errors.
- A redacted smoke report is recorded in ledger artifacts.

## Verification Plan

Use remote scripts that read secrets from files without printing them, `curl`/Python HTTP calls for REST checks, `entangled-ws-smoke` for WebSocket checks, direct cleanup verification for test rows, and sanitized log tail checks. Store the smoke report locally and remotely without secret values.

## Risks

- A write smoke against production must choose an entity and row ID that cannot collide with real data.
- WebSocket smoke behavior may depend on exact CLI arguments and service-token header support.
- If smoke cleanup fails, the row must be explicitly recorded and then removed before proceeding.

## Assumptions

- Production Entangled remains bound to `127.0.0.1:19900`.
- The service token file created during cutover remains valid.
- The deployed package includes `entangled.tools.ws_smoke` and/or the `entangled-ws-smoke` console entry point.
