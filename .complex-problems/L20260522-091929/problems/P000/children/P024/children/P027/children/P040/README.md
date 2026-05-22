# Build Entangled migration tooling and staging validation

## Problem

Before production cutover, Entangled needs an offline SQLite-to-Postgres migration tool and a test/staging validation path that proves schema, counts, sync versions, rowid replacement, transition IDs, REST behavior, and WebSocket sync semantics.

## Success Criteria

- Migration tool exports SQLite in read-only mode and imports into a clean `novaic_entangled` target.
- Migration preserves counts for all active inventory tables.
- Migration preserves `entangled_sync_versions` key/value pairs and `subagent_state_transitions` count/max ID.
- Migration copies SQLite `rowid` into Postgres `entangled_rowid` where stream/list semantics require it and resets sequences above migrated max values.
- Migration report records source/target counts and semantic checks without printing secrets.
- Staging/test Entangled can run in Postgres mode.
- REST smoke tests and WebSocket sync smoke tests pass against the staging/test Postgres target.
