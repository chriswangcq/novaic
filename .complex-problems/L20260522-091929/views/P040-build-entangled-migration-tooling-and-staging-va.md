# P040: Build Entangled migration tooling and staging validation

Status: done
Parent: P027
Root: P000
Source Ticket: T036 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040
Body: problems/P000/children/P024/children/P027/children/P040/README.md
Ticket(s): T045

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

## Subproblems
- P049: Build Entangled Offline Migration Command
- P050: Validate Entangled Migration Semantics Against Staging Data
- P051: Validate Entangled Postgres Mode With REST Smokes
- P052: Validate Entangled Postgres Mode With WebSocket Sync Smokes

## Results
- R057

## Latest Check
C059

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/README.md
- Ticket T045: problems/P000/children/P024/children/P027/children/P040/tickets/T045.md
- Result R057: problems/P000/children/P024/children/P027/children/P040/results/R057.md
- Check C059: problems/P000/children/P024/children/P027/children/P040/checks/C059.md

## Follow-ups
- none
