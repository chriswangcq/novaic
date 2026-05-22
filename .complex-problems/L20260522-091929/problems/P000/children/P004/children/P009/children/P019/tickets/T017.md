# Map Entangled SQLite Semantics to Postgres Requirements

## Problem Definition

Entangled uses SQLite as a dynamic entity store rather than as a fixed application schema. The Postgres migration must preserve database wrapper behavior, generated DDL, field serialization, CRUD/list/stream semantics, schema registration ordering, sync-version persistence, transition logs, and WebSocket/client expectations.

## Proposed Solution

Create one requirements artifact that maps each SQLite-era behavior to a concrete Postgres rule.

1. Inspect local source for:
   - `Database` connection, transaction, row, PRAGMA, and lock behavior.
   - `FieldDef` logical types and serialization.
   - `SqlEntityDef` generated table/index/alter SQL.
   - `SqlEntityStore` CRUD, list, list_stream, filtering, order, pagination, upsert, row conversion, defaults, and timestamp behavior.
   - `persistence.py` sync-version table, loading, and upsert callback.
   - `state_transitions.py` raw append/list transition-log semantics.
   - `app.factory`, `app.state`, `app.schema`, and `app.crud` startup/API paths.
2. Use the P018 live inventory to validate table groups and production row/version realities.
3. Define Postgres requirements for:
   - adapter boundary and DSN config;
   - transaction and lock behavior;
   - SQL placeholders and row mapping;
   - type mapping for JSON, bool, timestamp, integer identity, text ids, constraints, and indexes;
   - schema registration and additive migration ordering;
   - CRUD/list/list_stream/upsert SQL patterns;
   - sync-version monotonic persistence;
   - raw transition log identity/timestamp/JSON handling;
   - client sync compatibility risks.
4. Write `.complex-problems/L20260522-091929/artifacts/entangled-postgres-semantics.md`.

## Acceptance Criteria

- `Database` SQLite behavior is mapped to a Postgres adapter requirement.
- `FieldDef`, `SqlEntityDef`, and generated DDL/index behavior are mapped to Postgres type/constraint/index/additive migration rules.
- `SqlEntityStore` CRUD/list/list_stream/filter/order/pagination/upsert behavior is mapped to Postgres SQL patterns and adapter conventions.
- Schema registration ordering and idempotency are documented.
- `entangled_sync_versions` loading/upsert behavior is mapped to monotonic Postgres persistence.
- `subagent_state_transitions` raw table behavior is mapped to Postgres identity/index/JSON/timestamp requirements.
- Sync/client compatibility risks are documented for schema push, full sync, delta sync, reconnect, and ordering.
- No production Entangled migration or runtime change is attempted.

## Verification Plan

- Verify the artifact cites P018 inventory and the local source files inspected.
- Verify every P019 success criterion has a named section in the artifact.
- Verify the artifact distinguishes implementation requirements from production cutover steps.
- Record the result, then run a skeptical problem-level check.

## Risks

- A shallow SQL string replacement would miss placeholder, `rowid`, `lastrowid`, `PRAGMA`, and SQLite default behavior.
- Converting JSON/TIMESTAMP fields to native Postgres types can break existing wire shape if serialization is not kept stable.
- Enabling Postgres foreign keys where SQLite had `foreign_keys = OFF` may surface historical data inconsistencies.
- Sync versions that reset or move backward would break reconnect/full-delta expectations.
- Stream pagination currently depends on SQLite `rowid` tie-breaking; Postgres needs an explicit deterministic replacement.

## Assumptions

- P019 is requirements and semantics only; it does not implement a Postgres adapter or cut over production.
- P018 inventory is the authoritative current-state input for live table groups and row/version counts.
- Production and integration environments should target Postgres after migration; any SQLite remaining in development must be a narrow unit-test fake, not a second production logic path.
