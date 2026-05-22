# P100: Implement Queue SQLite To Postgres Copy Execution

Status: done
Parent: P075
Root: P000
Source Ticket: T096 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P075/children/P100
Body: problems/P000/children/P024/children/P028/children/P075/children/P100/README.md
Ticket(s): T098

## Problem
After planning exists, the migration must copy all active Queue tables from SQLite into a clean Postgres target while preserving identities and converting SQLite JSON text into native Postgres JSONB-compatible values. This must be implemented as reusable code rather than a one-off shell/manual procedure.

## Success Criteria
- Initializes or verifies the current Postgres Queue schema before copy.
- Copies every active Queue table and `config` from SQLite to Postgres in the planned order.
- Preserves primary keys, natural IDs, event/outbox integer IDs, idempotency keys, generations, and timestamps.
- Converts JSON text columns into native dict/list/scalar values for Postgres JSONB binding while leaving non-JSON fields unchanged.
- Fails safely on malformed JSON or unexpected target contents with a structured report error.
- Tests cover representative task/saga/session/lease/outbox/idempotency rows using fake Postgres execution and SQLite fixture input.

## Subproblems
- none

## Results
- R095

## Latest Check
C103

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P075/children/P100/README.md
- Ticket T098: problems/P000/children/P024/children/P028/children/P075/children/P100/tickets/T098.md
- Result R095: problems/P000/children/P024/children/P028/children/P075/children/P100/results/R095.md
- Check C103: problems/P000/children/P024/children/P028/children/P075/children/P100/checks/C103.md

## Follow-ups
- none
