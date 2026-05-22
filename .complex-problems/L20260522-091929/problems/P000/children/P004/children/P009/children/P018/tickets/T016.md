# Inventory Live Entangled SQLite State

## Problem Definition

Entangled's Postgres migration requirements must start from the live `api` host database rather than documentation or source assumptions. We need a read-only inventory of the active SQLite database, its runtime owners, sync-version state, table groups, schema/indexes, and health state.

## Proposed Solution

Collect a production-safe, read-only inventory from the `api` host and write a durable local artifact.

1. Identify the active Entangled service process, command-line database path, container/service context, and port/health endpoints.
2. Confirm the active SQLite file metadata and open file holders with read-only commands.
3. Query the SQLite database in read-only mode for:
   - table names and table DDL from `sqlite_master`;
   - index definitions and trigger definitions;
   - row counts for every table;
   - `entangled_sync_versions` count, min/max versions, and key summary;
   - transition-log row counts and max id/timestamp if present.
4. Map tables into groups:
   - dynamically registered entity tables;
   - `entangled_sync_versions`;
   - raw internal operational tables such as `subagent_state_transitions`;
   - SQLite internal tables.
5. Capture local code ownership pointers for Entangled database, schema, store, sync persistence, and transition-log modules.
6. Write `.complex-problems/L20260522-091929/artifacts/entangled-sqlite-inventory.md`.
7. Optionally copy the artifact to a documentation path on the `api` host, without changing service config, data, or runtime mode.

## Acceptance Criteria

- The active Entangled SQLite file path and service/process ownership are recorded.
- File metadata and open file holders are recorded.
- Health/readiness output is captured without exposing secrets.
- Complete table DDL, indexes, triggers, and row counts are recorded.
- `entangled_sync_versions` is summarized by count/key/version range without dumping sensitive payloads.
- Table groups and code ownership are mapped.
- A durable local inventory artifact exists.
- The result explicitly states that no production Entangled data, schema, service config, or runtime was mutated.

## Verification Plan

- Verify the inventory artifact exists and has non-empty schema and row-count sections.
- Verify the live service remains healthy/readiness-compatible after inventory collection.
- Verify `lsof` or equivalent holder output matches the identified process.
- Verify the result cites the artifact path and command classes used.

## Risks

- Entangled may be running outside Docker or under a shared `novaic` supervisor, so process discovery must not assume one container layout.
- The live DB path may differ from the default `data/entangled.db`.
- A live SQLite row-count snapshot can change while collecting; this is acceptable for inventory but must be labeled point-in-time.
- Health endpoints or command lines may include sensitive tokens; redact secrets in artifacts and final summaries.

## Assumptions

- Inventory commands are read-only except for writing the local artifact and optional documentation copy.
- The `api` host is reachable through the same SSH path used earlier in this ledger.
- P018 does not migrate data or alter Entangled runtime configuration.
