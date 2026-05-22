# Validate Entangled Migration Semantics Against Staging Data

## Problem

After the migration command exists, it must be proven against fixture or staging data that the copied Postgres target semantically matches the SQLite source. This belongs under `P040` because row counts alone are not enough; sync versions, transition IDs, rowid replacement, JSON/BOOL/TIMESTAMP shape, and sequence state must be checked before production cutover.

## Success Criteria

- A validation path runs the migration against a safe non-production target or fixture-backed Postgres-compatible target.
- Source and target row counts match for every active migrated table.
- Every `entangled_sync_versions` `state_key` and `version` matches exactly.
- `subagent_state_transitions` count and max ID match exactly.
- Each migrated dynamic table with stream/list semantics has `entangled_rowid` populated for every copied row, with values matching SQLite `rowid`.
- Representative JSON, BOOL, BLOB, INTEGER, REAL, and TIMESTAMP values are checked for expected Postgres storage and API-facing wire shape where data exists.
- Sequence checks prove the next generated ID is greater than migrated max values.
- A redacted validation report is written as a ledger artifact and contains no DSNs, passwords, tokens, or env-file contents.
