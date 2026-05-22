# Build Reproducible Entangled WebSocket Smoke Client

## Problem Definition

`P061` needs a reproducible WebSocket smoke client or command that can connect to Entangled `/v1/sync` in Postgres staging mode and capture protocol evidence for `P062`. The client must authenticate without leaking tokens, parse frame types/counts, drive or observe a write/delta path, support reconnect checks, and record stream-order evidence involving `entangled_rowid`.

## Proposed Solution

Inspect the Entangled WebSocket protocol implementation and add a small smoke script under `Entangled/packages/server-python/scripts/` or an equivalent test-support path. The script should accept endpoint, token-file or JWT-secret-file, user id, entity names, and output path arguments. It should authenticate with an Authorization-header JWT, avoid query-string tokens, collect schema/full/head/push frames as available, optionally issue REST writes through `X-Service-Token`, reconnect after a controlled disconnect, query staging Postgres counts/rowids only through redacted inputs, and emit a JSON report that stores statuses/counts rather than secret values.

## Acceptance Criteria

- A documented command/script connects to a configurable `/v1/sync` endpoint using Authorization-header JWT auth.
- The script reads secrets from files or environment variables and does not print raw token/JWT/DSN values.
- Frame parsing records frame types, entity names, and counts for schema/full/head/push or closest available protocol frames.
- The script can trigger or observe a write/delta path for the staging smoke entities.
- The script can perform a disconnect/reconnect sequence.
- The script can record stream-order evidence for `ws-smoke-stream-events` without embedding payload secrets.
- Local tests, dry-run mode, or a safe staging dry run verifies redaction and basic protocol handling.

## Verification Plan

Run targeted local tests or `py_compile` for the script, then run a safe dry-run or minimal staging invocation against the already prepared `P060` runtime. Confirm the output JSON has no raw secrets and contains enough protocol fields for `P062` to make success/failure judgments.

## Risks

- The WebSocket protocol may require specific client messages beyond a basic handshake.
- The available server frames may differ from the success criteria names, requiring careful mapping to the closest protocol evidence.
- Running REST writes from the script must avoid mutating production data and must stay on the dedicated staging endpoint.

## Assumptions

- `P060` leaves a Postgres-mode staging runtime running on loopback port `19910`.
- The staging token file can be used both as service token for REST writes and as JWT signing secret for WebSocket auth.
- `P062` will own the full execution report and final runtime cleanup.
