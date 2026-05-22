# Port Entangled sync-version and transition-log persistence to Postgres

## Problem

Entangled support tables `entangled_sync_versions` and `subagent_state_transitions` currently use SQLite DDL and upsert/identity behavior. Port these support tables to Postgres while preserving sync-version monotonicity and transition atomicity.

## Success Criteria

- `entangled_sync_versions` Postgres DDL uses `state_key text primary key` and `version bigint`.
- Version persistence uses monotonic upsert so older versions cannot overwrite newer versions.
- `subagent_state_transitions` Postgres DDL uses a generated identity `bigint` ID and preserves append-only columns.
- Transition update plus history insert remains atomic under the existing transaction boundary.
- Migration expectations for resetting transition identity above migrated max ID are documented or implemented in support helpers.
- Tests cover monotonic version upsert, rollback on failed transition, and row-shape compatibility.
- Existing SQLite support-table behavior remains passing.
