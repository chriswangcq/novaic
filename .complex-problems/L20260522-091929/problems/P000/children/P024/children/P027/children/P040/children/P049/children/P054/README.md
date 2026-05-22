# Implement Entangled Migration Copy Executor And Identity Reset

## Problem

After planning exists, the migration tool needs execution logic that copies data into Postgres using explicit columns, migrates support tables exactly, preserves `entangled_rowid`, and resets generated identities above migrated max values. This belongs under `P049` because the migration command is not useful until the planned copy can actually execute through the Entangled database boundary.

## Success Criteria

- A migration executor module/function copies planned dynamic entity tables with explicit source and target columns.
- When a planned target has `entangled_rowid`, copied rows use SQLite `rowid` as `entangled_rowid`.
- `entangled_sync_versions` copies all `state_key`/`version` rows exactly.
- `subagent_state_transitions` copies all append-only rows and captures count/max ID.
- Sequence reset statements are executed or emitted for dynamic identity IDs and `subagent_state_transitions` after import.
- Target counts and semantic check results are returned to the report model.
- Focused tests cover generated insert column lists, rowid copy behavior, support-table copy behavior, sequence reset calls, and target count reporting with fake adapters or fixtures.
