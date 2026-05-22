# Port Entangled dynamic schema and entity semantics to Postgres

## Problem Definition

Entangled now has an explicit Postgres adapter boundary, but its schema generator, entity store, sync-version persistence, and transition-log SQL are still SQLite-oriented. Port those semantics to Postgres while preserving dynamic schema registration, row shapes, JSON/BOOL/TIMESTAMP behavior, stream ordering, sync-version monotonicity, and transition atomicity.

## Proposed Solution

Split this into focused implementation slices:

1. Add a Postgres DDL dialect for `FieldDef`/`SqlEntityDef`, including safe identifier handling, field-type mapping, catalog-based existing-column inspection, index creation, and support-table DDL for sync versions and transitions.
2. Port `SqlEntityStore` query construction to dialect-aware SQL for CRUD, upsert, update/delete/CAS, list, list_stream, cleanup, default filters, parent scoping, and hidden-field output.
3. Preserve SQLite `rowid`-dependent stream/list cleanup semantics with an explicit `entangled_rowid` tie-break column in Postgres.
4. Port support-table logic for `entangled_sync_versions` and `subagent_state_transitions`, including monotonic upsert, generated identity IDs, rollback behavior, and sequence reset expectations.
5. Expand tests to cover schema registration, DDL generation for live table shapes, JSON/BOOL/TIMESTAMP round trips, stream ordering with duplicate cursor values, sync-version monotonicity, transition atomicity, and SQLite compatibility.

## Acceptance Criteria

- Entangled can register representative production schemas under a Postgres dialect without SQLite-only `PRAGMA`, `AUTOINCREMENT`, `datetime('now')`, or `rowid` assumptions.
- Dynamic entity CRUD/upsert/list/list_stream/update/delete/CAS SQL can run against the Postgres adapter interface.
- JSONB, boolean, bytea, integer/bigint, real, and timestamp-like fields preserve current API row shapes.
- Stream pagination and cleanup use `entangled_rowid` instead of SQLite `rowid` while preserving ordering semantics.
- `entangled_sync_versions` uses monotonic Postgres upsert semantics.
- `subagent_state_transitions` preserves atomic update-plus-log behavior and generated identity IDs.
- SQLite mode remains compatible until the production cutover child removes active SQLite runtime use.
- Tests and compile checks pass.

## Verification Plan

Run dialect unit tests, entity-store behavior tests with adapter fakes, existing SQLite tests, and py_compile. Where possible, run a local or fake Postgres adapter contract that captures generated SQL and verifies Postgres-specific statements. Defer real staging integration against `novaic_entangled` to P040.

## Risks

- Query conversion is broad and subtle; scattered ad hoc SQL replacement could break row shape or filtering.
- `rowid` replacement must be comprehensive or stream pagination can duplicate/skip rows.
- Timestamp normalization may accidentally change client-visible JSON/API values.
- Turning SQLite foreign-key clauses into enforced Postgres constraints too early could reject existing production data.

## Assumptions

- P038 adapter/runtime boundary is complete.
- First Postgres cutover can defer foreign-key enforcement hardening.
- Timestamp-like wire output should be preserved for this migration rather than normalized as a behavior change.
