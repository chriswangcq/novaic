# P054: Implement Entangled Migration Copy Executor And Identity Reset

Status: done
Parent: P049
Root: P000
Source Ticket: T046 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P054
Body: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P054/README.md
Ticket(s): T048

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

## Subproblems
- none

## Results
- R044

## Latest Check
C045

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P054/README.md
- Ticket T048: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P054/tickets/T048.md
- Result R044: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P054/results/R044.md
- Check C045: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P054/checks/C045.md

## Follow-ups
- none
