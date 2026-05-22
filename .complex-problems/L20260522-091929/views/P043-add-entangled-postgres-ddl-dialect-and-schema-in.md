# P043: Add Entangled Postgres DDL dialect and schema inspection

Status: done
Parent: P039
Root: P000
Source Ticket: T038 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P039/children/P043
Body: problems/P000/children/P024/children/P027/children/P039/children/P043/README.md
Ticket(s): T039

## Problem
Entangled's current `SqlEntityDef` and `FieldDef` emit SQLite DDL and rely on `PRAGMA table_info`. Add a Postgres dialect for dynamic schema registration without breaking current SQLite behavior.

## Success Criteria
- `FieldDef` can render Postgres column DDL for all supported field kinds.
- `SqlEntityDef` can render Postgres `CREATE TABLE`, missing-column `ALTER TABLE`, and index SQL.
- Postgres dynamic tables include `entangled_rowid` where needed for rowid replacement.
- Existing-column inspection for Postgres uses catalog/information-schema data instead of SQLite `PRAGMA`.
- Identifier validation/quoting prevents unsafe table or column interpolation.
- Representative live inventory schemas generate expected Postgres DDL.
- SQLite DDL behavior remains unchanged and existing tests pass.

## Subproblems
- none

## Results
- R036

## Latest Check
C037

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P039/children/P043/README.md
- Ticket T039: problems/P000/children/P024/children/P027/children/P039/children/P043/tickets/T039.md
- Result R036: problems/P000/children/P024/children/P027/children/P039/children/P043/results/R036.md
- Check C037: problems/P000/children/P024/children/P027/children/P039/children/P043/checks/C037.md

## Follow-ups
- none
