# Build Entangled WebSocket Sync Smoke Client

## Problem

The current WebSocket protocol shape must be exercised by a reproducible command or script rather than manual observation. Inspect the Entangled server/client protocol enough to build or adapt a small smoke client that connects to `/v1/sync`, authenticates without exposing secrets, records frame types/counts, and can drive the checks required by `P052`. This belongs under `P052` because production cutover needs repeatable WebSocket proof, not only REST or offline SQL checks.

## Success Criteria

- The smoke client or documented command connects to a configurable Entangled WebSocket endpoint with a token read from a file or environment variable.
- The client records schema/full/head or closest available protocol frames with entity names and counts.
- The client can trigger or observe a write/delta path for representative entities.
- The client can test controlled disconnect/reconnect behavior.
- The client records enough stream ordering evidence to detect duplicate or skipped rows involving `entangled_rowid`.
- Local tests, dry-run checks, or protocol-level validation cover redaction and frame parsing without requiring production secrets.
