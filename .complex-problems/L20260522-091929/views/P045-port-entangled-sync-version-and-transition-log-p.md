# P045: Port Entangled sync-version and transition-log persistence to Postgres

Status: done
Parent: P039
Root: P000
Source Ticket: T038 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P039/children/P045
Body: problems/P000/children/P024/children/P027/children/P039/children/P045/README.md
Ticket(s): T044

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

## Subproblems
- none

## Results
- R041

## Latest Check
C042

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P039/children/P045/README.md
- Ticket T044: problems/P000/children/P024/children/P027/children/P039/children/P045/tickets/T044.md
- Result R041: problems/P000/children/P024/children/P027/children/P039/children/P045/results/R041.md
- Check C042: problems/P000/children/P024/children/P027/children/P039/children/P045/checks/C042.md

## Follow-ups
- none
