# P094: Port Session Rebuild And Read Models To Postgres

Status: todo
Parent: P082
Root: P000
Source Ticket: T088 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P094
Body: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P094/README.md
Ticket(s): none

## Problem
Session rebuild and read-model queries were shaped around SQLite tables, JSON text, and implicit ordering. The Postgres runtime needs deterministic ordering, backend-aware SQL, native JSONB/timestamptz handling, and a clear startup serialization rule so rebuild does not race live dispatch.

## Success Criteria
- Session active-state reads, pending-input reads, and outbox/session projections use deterministic `created_at, id` or equivalent stable ordering under Postgres.
- Postgres rebuild uses explicit row/advisory locking or an enforced single-rebuild startup boundary before live dispatch traffic.
- Rebuild reads running saga/session state through Postgres-safe SQL and native JSON/timestamp values without SQLite JSON functions.
- Rebuild writes session state through the same authoritative ledger/store boundary used by normal session transitions.
- Focused tests cover deterministic rebuild ordering, active session reconstruction, and absence of SQLite-only SQL in the Postgres session read path.
- Any remaining SQLite read SQL is isolated in adapter helpers, not interleaved with Postgres business flow.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P094/README.md

## Follow-ups
- none
