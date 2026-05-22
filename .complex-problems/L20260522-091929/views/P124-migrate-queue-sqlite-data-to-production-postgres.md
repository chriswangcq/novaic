# P124: Migrate Queue SQLite Data To Production Postgres And Verify

Status: todo
Parent: P077
Root: P000
Source Ticket: T120 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P124
Body: problems/P000/children/P024/children/P028/children/P077/children/P124/README.md
Ticket(s): none

## Problem
The production SQLite queue contents must be copied into `novaic_queue` with schema version, row counts, JSON payloads, FSM projections, outbox state, lease state, and idempotency semantics verified before services restart on Postgres.

## Success Criteria
- Migration tooling runs against the frozen SQLite backup/source and production Postgres target.
- Row counts match expected source-to-target mappings for all Queue tables.
- Semantic invariant checks cover task state, saga state, session/outbox rows, worker lease rows, and idempotency completed/in-progress rows.
- Any migration warnings or skipped rows are recorded and resolved or block cutover.
- A redacted migration report is saved under ledger artifacts.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P124/README.md

## Follow-ups
- none
