# P134: Verify Production Queue Postgres Migration Semantics

Status: done
Parent: P124
Root: P000
Source Ticket: T128 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P134
Body: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P134/README.md
Ticket(s): T131

## Problem
After the data copy, production Postgres must be checked against the frozen SQLite backup for row counts and semantic invariants before Queue services restart. This belongs under P124 because raw migration completion is insufficient without proof that task state, saga state, FSM projections, outbox/session state, leases, and idempotency semantics survived correctly.

## Success Criteria
- Source SQLite and target Postgres row counts are compared for all migrated Queue tables.
- Semantic checks cover task state, saga state, FSM projections, session/outbox rows, worker lease rows, and idempotency completed/in-progress rows.
- Schema/version metadata is verified on the Postgres target.
- Any count mismatch or semantic warning is resolved or recorded as a blocker.
- A redacted verification report is saved under ledger artifacts.

## Subproblems
- none

## Results
- R127

## Latest Check
C142

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P134/README.md
- Ticket T131: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P134/tickets/T131.md
- Result R127: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P134/results/R127.md
- Check C142: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P134/checks/C142.md

## Follow-ups
- none
