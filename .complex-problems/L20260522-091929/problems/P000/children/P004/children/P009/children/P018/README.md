# Inventory Entangled SQLite Schema and Runtime Owners

## Problem

Before designing the Postgres migration, the live `entangled.db` on the `api` host must be treated as authoritative. We need a read-only inventory of its schema, table groups, indexes, row counts, sync-version rows, transition logs, health/readiness state, and active process owners so later requirements do not rely on stale docs or local assumptions.

This belongs under P009 because live inventory is the foundation for preserving Entangled entity state and sync behavior during migration.

## Success Criteria

- The live Entangled SQLite database path, file metadata, health/readiness response, process command line, and open file holders are captured from the `api` host.
- Complete live table DDL, indexes, triggers, and row counts are recorded.
- Registered entity tables, `entangled_sync_versions`, and raw internal tables such as `subagent_state_transitions` are identified.
- `entangled_sync_versions` keys and version ranges/counts are summarized without dumping sensitive payloads.
- A durable local artifact exists under the ledger artifacts directory, and any server-side operator copy is read-only documentation.
- No production Entangled table, row, schema, config, or runtime mode is changed.
