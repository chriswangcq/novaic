# Entangled Support Table Postgres Port Result

## Summary

`T044` ported Entangled sync-version and subagent transition support tables to backend-aware SQLite/Postgres SQL while preserving the existing SQLite behavior. The implementation is local-only at this layer; production deployment and data migration remain owned by later cutover tickets.

## Done

- Added Postgres-aware sync-version DDL and upsert SQL in `Entangled/packages/server-python/entangled/sql/persistence.py`.
- Preserved SQLite sync-version replacement semantics while making Postgres use monotonic `GREATEST(existing, excluded)` version updates.
- Added Postgres-aware subagent transition-log DDL in `Entangled/packages/server-python/entangled/sql/state_transitions.py`.
- Added a Postgres identity reset helper for transition-log migration/cutover work.
- Added focused coverage in `Entangled/packages/server-python/tests/test_postgres_support_tables.py`.

## Verification

- `python -m pytest tests/test_postgres_support_tables.py tests/test_state_transitions.py tests/test_sync_snapshot.py` passed: 14 tests.
- `python -m py_compile entangled/sql/persistence.py entangled/sql/state_transitions.py` passed.
- `python -m pytest` passed for the full Entangled server-python suite: 105 tests.

## Known Gaps

- This ticket does not perform real Postgres staging migration or production cutover.
- This ticket does not remove SQLite files or old Entangled runtime state; cleanup belongs to later migration and cutover tickets.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/persistence.py`
- `Entangled/packages/server-python/entangled/sql/state_transitions.py`
- `Entangled/packages/server-python/tests/test_postgres_support_tables.py`
