# Cortex Operational Postgres Cutover

## Problem Definition

Cortex still stores active operational state in `/opt/novaic/data/cortex/operational.sqlite3`. This state is durable operational control-plane data, not disposable cache. It must move to the existing `novaic_cortex` Postgres database while preserving operational event, projection, active-stack, and payload-manifest behavior.

## Proposed Solution

Split Cortex cutover into code/storage implementation and production execution:

1. Implement Cortex Postgres operational store.
   - Add Postgres schema/adapter/config support.
   - Preserve current `OperationalSqliteStore` behavior for all five tables.
   - Preserve idempotency and projection semantics.
   - Add focused tests for the store contract.
2. Migrate and cut over production Cortex.
   - Back up `/opt/novaic/data/cortex/operational.sqlite3`.
   - Copy all five tables into `novaic_cortex`.
   - Switch Cortex startup config to Postgres.
   - Restart and verify `/health`, `/ready`, representative operational endpoints, and row counts.
   - Update central classification and rollback notes.

## Acceptance Criteria

- Cortex production runtime uses `novaic_cortex` for operational state.
- All five operational tables are migrated with row-count checks.
- Idempotency keys, event ordering, projections, active stack, and payload manifest behavior are preserved.
- Cortex health/readiness pass after cutover.
- Old operational SQLite is moved or labeled rollback-only.
- Central classification note is updated.

## Verification Plan

- Inspect current Cortex operational store and tests before editing.
- Run focused Cortex tests after implementation.
- Run production preflight before restart/cutover.
- Compare SQLite and Postgres row counts for all five tables.
- Verify Cortex readiness and representative operational reads after restart.

## Risks

- Active-stack/projection semantics can affect runtime control flow.
- `scope_events.idempotency_key` behavior must remain unique but nullable.
- JSON fields must keep API-compatible output shape.
- Restarting Cortex as part of the shared service can briefly interrupt agent/runtime workflows.

## Assumptions

- `novaic_cortex` database/user already exists.
- Workspace/Blob/LogicalFS data remains outside this operational DB migration.
