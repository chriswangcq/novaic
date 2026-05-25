# Entangled updated_at fix result

## Summary

Implemented a SQL-store invariant in Entangled: automatic `updated_at` assignment is appended only when the update payload does not already include `updated_at`. This removes the production Postgres error that blocked Environment notification claim.

## Done

- Added `SqlEntityStore._should_auto_set_updated_at`.
- Applied the rule to:
  - `_sql_update`
  - `_sql_upsert`
  - `batch_update`
  - `update_where`
  - `cas_update`
- Added Postgres SQL-generation tests for explicit `updated_at` in all affected mutation paths.
- Verified existing automatic timestamp behavior still has coverage for update/upsert without explicit `updated_at`.

## Verification

- `python3 -m pytest packages/server-python/tests/test_postgres_entity_write_queries.py`
  - Result: `10 passed`
- `python3 -m pytest packages/server-python/tests`
  - Result: `68 passed`

## Known Gaps

- The fix is not yet committed or deployed.
- Production subscriber recovery and end-to-end chat response remain to be validated in P003.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/entity_store.py`
- `Entangled/packages/server-python/tests/test_postgres_entity_write_queries.py`
