# Add Entangled Postgres DDL dialect and schema inspection

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
