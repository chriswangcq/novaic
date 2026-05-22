# Design Entangled Postgres Migration Requirements

## Problem

`entangled.db` owns entity state, schema registration, sync versions, and sync-facing projections. Migrating it to Postgres requires preserving JSON entity behavior, schema registration order, sync-version monotonicity, and WebSocket/client expectations.

This belongs under P004 because Entangled is a separate current state owner with different risks from queue.

## Success Criteria

- Entangled SQLite schema and entity-store code paths are mapped to Postgres requirements.
- Schema registration and `entangled_sync_versions` behavior are documented.
- Sync/client compatibility risks and rollback strategy are identified.
- A migration implementation plan exists with pre/post row and version checks.
- No production Entangled cutover is attempted by this problem.
