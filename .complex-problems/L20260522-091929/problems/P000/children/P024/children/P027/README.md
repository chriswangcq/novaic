# Implement Entangled Postgres Cutover

## Problem

Entangled still owns active entity, sync, chat, device, model, execution, and user state in `/opt/novaic/data/entangled.db`. It should be migrated to the existing `novaic_entangled` Postgres database while preserving schema registration, sync-version monotonicity, row shapes, and transition atomicity.

## Success Criteria

- Entangled has a Postgres-backed production store for all active tables identified in P009.
- Schema registration and `entangled_sync_versions` behavior are preserved.
- Entity row shapes, JSON behavior, API responses, and sync/client expectations remain compatible.
- Existing Entangled SQLite state is backed up and migrated with row-count, max-version, and representative API checks.
- Entangled runtime config is switched to Postgres and health/readiness/WebSocket smoke checks pass.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.
