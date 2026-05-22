# Port Entangled basic CRUD/upsert write queries to Postgres

## Problem

Add dialect-aware query helpers for create/get/update/delete/upsert/CAS/update_where/delete_where so Postgres paths avoid SQLite-only SQL while preserving SQLite behavior.

## Success Criteria

- Postgres create paths use `RETURNING` for auto-integer IDs.
- Postgres update/upsert paths avoid SQLite-only timestamp expressions.
- Rowcount-driven update/delete/CAS results remain preserved.
- `_scope_where`, parent filters, key params, and user scoping continue to generate correct predicates.
- SQLite behavior remains unchanged and tests pass.
- Focused fake-Postgres SQL capture tests cover create/update/upsert/delete/CAS query generation.
