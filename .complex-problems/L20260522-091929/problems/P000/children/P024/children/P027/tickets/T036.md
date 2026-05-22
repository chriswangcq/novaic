# Implement Entangled Postgres cutover

## Problem Definition

Entangled still uses `/opt/novaic/data/entangled.db` as the active production state owner for dynamic entities, sync versions, schema registration, transition logs, users, devices, agents, chat, models, and execution state. It must move to the existing `novaic_entangled` Postgres database without keeping a production SQLite fallback or breaking Entangled's dynamic schema, sync, stream pagination, row-shape, and WebSocket semantics.

## Proposed Solution

Split the work into implementation, preflight, and production cutover:

1. Implement a Postgres Entangled DB adapter behind the existing DB boundary, with connection pooling, dict-like rows, transaction semantics, advisory-lock compatibility, rowcount behavior, and `RETURNING` support.
2. Add a Postgres DDL dialect for `SqlEntityDef`/`FieldDef`, including safe identifiers, catalog inspection, `jsonb`/`boolean`/`bytea` mappings, identity columns, and `entangled_rowid` for SQLite `rowid`-dependent stream semantics.
3. Convert entity-store SQL paths to Postgres-safe operations while preserving CRUD, upsert, filters, stream pagination, JSON/BOOL/TIMESTAMP wire shape, hidden-field behavior, rowcount results, and CAS semantics.
4. Preserve `entangled_sync_versions` monotonicity and `subagent_state_transitions` atomicity, including sequence reset after migration.
5. Build a migration tool that exports SQLite with row counts, rowid, sync-version values, transition max IDs, and imports into a clean `novaic_entangled` with validation reports.
6. Validate in a test/staging Postgres environment with REST and WebSocket smoke tests.
7. Execute production cutover in a writer-free window: back up SQLite, stop Entangled/upstream writers, import to Postgres, switch runtime config, restart, verify health/readiness/REST/WS behavior, then move old SQLite out of the active path only after no-holder checks.

## Acceptance Criteria

- Production Entangled runs on `novaic_entangled` Postgres with no active SQLite writer.
- All active tables identified by the Entangled inventory are migrated with matching row counts.
- `entangled_sync_versions` keys/versions are equal after migration and cannot regress under older updates.
- `subagent_state_transitions` count and max identity value are preserved and future inserts continue above the migrated max ID.
- Dynamic schema registration remains idempotent in Postgres.
- Entity REST reads/writes preserve row shapes, JSON/BOOL/TIMESTAMP behavior, hidden-field masking, and stream ordering.
- WebSocket sync can connect, receive schemas, perform representative sync/list/form/stream paths, and continue after restart.
- Old `/opt/novaic/data/entangled.db*` files are retained only as rollback evidence and documented in the central classification note.

## Verification Plan

Run adapter contract tests, entity-store behavior tests, DDL inventory checks, migration dry-run checks, and staging integration tests before production. For production, capture pre-cutover counts and sync-version/max-id evidence, run the migration into a clean target, compare counts and invariants, restart Entangled in Postgres mode, run health/readiness/REST/WebSocket smokes, check process args and file holders, then clean the active SQLite path and write rollback/classification notes.

## Risks

- Entangled is a dynamic-schema service, so string-level SQL conversion can cause subtle regressions if not centralized.
- SQLite `rowid` semantics are observable through stream pagination and cleanup ordering.
- WebSocket sync-version mistakes can cause missed updates or excessive full syncs.
- Turning on Postgres constraints too early could reject data that SQLite accepted with foreign keys disabled.
- Production cutover requires freezing writers to avoid dual-source divergence.

## Assumptions

- The P018 inventory and P019 semantic mapping remain valid enough to drive implementation.
- First cutover may preserve timestamp-like wire output rather than normalizing all timestamps immediately.
- Foreign-key hardening can be deferred until after a data audit.
- The existing `novaic_entangled` database/user from P001 remains available.
