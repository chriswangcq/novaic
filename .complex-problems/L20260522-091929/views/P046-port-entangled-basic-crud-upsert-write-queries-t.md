# P046: Port Entangled basic CRUD/upsert write queries to Postgres

Status: done
Parent: P044
Root: P000
Source Ticket: T040 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P046
Body: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P046/README.md
Ticket(s): T041

## Problem
Add dialect-aware query helpers for create/get/update/delete/upsert/CAS/update_where/delete_where so Postgres paths avoid SQLite-only SQL while preserving SQLite behavior.

## Success Criteria
- Postgres create paths use `RETURNING` for auto-integer IDs.
- Postgres update/upsert paths avoid SQLite-only timestamp expressions.
- Rowcount-driven update/delete/CAS results remain preserved.
- `_scope_where`, parent filters, key params, and user scoping continue to generate correct predicates.
- SQLite behavior remains unchanged and tests pass.
- Focused fake-Postgres SQL capture tests cover create/update/upsert/delete/CAS query generation.

## Subproblems
- none

## Results
- R037

## Latest Check
C038

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P046/README.md
- Ticket T041: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P046/tickets/T041.md
- Result R037: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P046/results/R037.md
- Check C038: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P046/checks/C038.md

## Follow-ups
- none
