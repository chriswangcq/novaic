# Implement Cortex Operational Postgres Cutover

## Problem

Cortex still owns active durable operational state in `/opt/novaic/data/cortex/operational.sqlite3`. It should be migrated to the existing `novaic_cortex` Postgres database while preserving event, projection, active-stack, and payload-manifest behavior.

## Success Criteria

- Cortex has a Postgres-backed production operational store.
- All five operational tables are migrated: `cortex_operational_meta`, `scope_events`, `scope_projection`, `active_stack_projection`, and `payload_manifest`.
- Idempotency keys, active-stack semantics, projection reads, and payload manifest behavior are preserved.
- Existing Cortex SQLite state is backed up and migrated with row-count and semantic checks.
- Cortex runtime config is switched to Postgres and health/readiness/API smoke checks pass.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.
