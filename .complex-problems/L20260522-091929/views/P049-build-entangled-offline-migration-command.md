# P049: Build Entangled Offline Migration Command

Status: done
Parent: P040
Root: P000
Source Ticket: T045 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P049
Body: problems/P000/children/P024/children/P027/children/P040/children/P049/README.md
Ticket(s): T046

## Problem
Entangled needs an offline SQLite-to-Postgres migration command that can safely read the SQLite source, create or replace a clean Postgres target schema, copy dynamic entity rows and support tables, preserve stream ordering via `entangled_rowid`, reset identities, and produce a redacted report. This belongs under `P040` because staging validation cannot be meaningful until the migration command exists.

## Success Criteria
- A migration command or module exists under `Entangled/packages/server-python/scripts/` or an equivalent package path.
- The command opens the SQLite source in read-only mode and refuses ambiguous destructive Postgres target cleanup without an explicit clean-target flag.
- The command registers or creates Postgres schemas using the Entangled schema/DDL path rather than hand-written table-only shortcuts.
- Dynamic entity tables copy SQLite `rowid` into Postgres `entangled_rowid` wherever that column exists.
- `entangled_sync_versions` and `subagent_state_transitions` are migrated with exact key/value and count/max-ID preservation.
- Postgres identity sequences for dynamic IDs and transition IDs are reset above migrated maximum values.
- The command emits a structured migration report with redacted connection information, source counts, target counts, sequence reset evidence, semantic checks, and skipped tables with reasons.
- Focused unit tests cover planning, rowid copy, support-table migration, sequence reset SQL, report redaction, and refusal of unsafe target cleanup.

## Subproblems
- P053: Build Entangled Migration Planner And Redacted Report Model
- P054: Implement Entangled Migration Copy Executor And Identity Reset
- P055: Add Entangled Migration CLI Entry Point And Test Coverage
- P056: Add Entangled Migration Target Schema Preparation And Clean-Target Execution

## Results
- R046

## Latest Check
C049

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P049/README.md
- Ticket T046: problems/P000/children/P024/children/P027/children/P040/children/P049/tickets/T046.md
- Result R046: problems/P000/children/P024/children/P027/children/P040/children/P049/results/R046.md
- Check C047: problems/P000/children/P024/children/P027/children/P040/children/P049/checks/C047.md
- Check C049: problems/P000/children/P024/children/P027/children/P040/children/P049/checks/C049.md

## Follow-ups
- P056: Add Entangled Migration Target Schema Preparation And Clean-Target Execution
