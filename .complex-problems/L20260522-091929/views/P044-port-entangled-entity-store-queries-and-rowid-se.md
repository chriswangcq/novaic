# P044: Port Entangled entity-store queries and rowid semantics to Postgres

Status: done
Parent: P039
Root: P000
Source Ticket: T038 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P039/children/P044
Body: problems/P000/children/P024/children/P027/children/P039/children/P044/README.md
Ticket(s): T040

## Problem
`SqlEntityStore` query construction is SQLite-specific across CRUD, upsert, list, stream pagination, cleanup, timestamp updates, and `rowid` tie-breaks. Add dialect-aware query paths for Postgres while preserving API row shapes and existing SQLite behavior.

## Success Criteria
- CRUD/create/get/update/delete/upsert/CAS/list/list_stream/update_where/delete_where/cleanup paths generate Postgres-safe SQL.
- SQLite `rowid` comparisons and orderings are replaced by `entangled_rowid` in Postgres.
- JSON, BOOL, BLOB, INTEGER, REAL, and TIMESTAMP input/output behavior matches current API row shapes.
- Parent/user/key-param scoping, `filters`, `in_filters`, `not_in_filters`, defaults, hidden fields, and `has_<hidden>` behavior are preserved.
- Auto-integer IDs use `RETURNING` in Postgres.
- Existing SQLite behavior remains covered and passing.
- Focused tests cover duplicate cursor values, rowid tie-break migration semantics, JSON/BOOL round trip, and rowcount-driven updates/deletes.

## Subproblems
- P046: Port Entangled basic CRUD/upsert write queries to Postgres
- P047: Port Entangled stream pagination and cleanup rowid semantics to Postgres
- P048: Preserve Entangled row output shape under Postgres query paths

## Results
- R040

## Latest Check
C041

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P039/children/P044/README.md
- Ticket T040: problems/P000/children/P024/children/P027/children/P039/children/P044/tickets/T040.md
- Result R040: problems/P000/children/P024/children/P027/children/P039/children/P044/results/R040.md
- Check C041: problems/P000/children/P024/children/P027/children/P039/children/P044/checks/C041.md

## Follow-ups
- none
