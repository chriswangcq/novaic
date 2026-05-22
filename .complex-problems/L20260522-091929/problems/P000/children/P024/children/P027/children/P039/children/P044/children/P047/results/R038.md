# Entangled stream rowid semantics result

## Summary

P047 ported Entangled stream pagination and cleanup tie-break semantics to Postgres. SQLite paths still use `rowid`, while Postgres paths use the explicit `entangled_rowid` column added by the DDL dialect.

## Done

- Added `SqlEntityStore._rowid_column()` and backend-aware order normalization.
- Changed `list_stream` before-cursor lookup to select `entangled_rowid AS _rid` in Postgres mode.
- Changed `list_stream` and `exists_before` cursor predicates to compare `entangled_rowid` in Postgres mode.
- Changed cleanup fallback ordering to use `entangled_rowid DESC` in Postgres mode.
- Extended order-by validation with explicit extra internal fields instead of globally allowing arbitrary unknown keys.
- Added focused SQL-capture tests for Postgres and SQLite stream rowid behavior.

## Verification

- Targeted tests passed: `15 passed`.
- Full Entangled test suite passed: `95 passed`.
- py_compile passed for touched stream/validation modules.

## Known Gaps

- Output-shape cross-checks are intentionally deferred to P048.
- Migration tooling must still copy SQLite `rowid` values into `entangled_rowid`.
- Real Postgres execution is deferred to staging validation.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/entity_store.py`
- `Entangled/packages/server-python/entangled/sql/validation.py`
- `Entangled/packages/server-python/tests/test_postgres_stream_rowid_queries.py`
