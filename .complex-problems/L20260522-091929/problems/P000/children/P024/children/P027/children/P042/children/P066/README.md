# Run Entangled Production Postgres REST And WebSocket Smokes

## Problem

After production Entangled starts in Postgres mode, representative REST and WebSocket behavior must be verified before active SQLite files are moved out of the production path. This belongs under `P042` because runtime health alone is not enough to prove the cutover works.

## Success Criteria

- Representative REST read smoke passes against production Postgres-mode Entangled.
- A bounded REST write/update/delete or explicitly safe equivalent passes without corrupting production data.
- WebSocket schema/list/stream/delta/reconnect smoke passes or records the smallest justified direct protocol equivalent.
- Postgres counts or key semantic values remain sane after smokes.
- Reports/log checks confirm no raw DSN/token/JWT values are recorded.
- Any smoke-created production test rows are cleaned up or explicitly marked harmless.
