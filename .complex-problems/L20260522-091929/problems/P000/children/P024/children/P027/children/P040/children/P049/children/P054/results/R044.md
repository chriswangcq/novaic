# Entangled Migration Copy Executor And Identity Reset Result

## Summary

`T048` implemented the local migration execution layer on top of the planner/report model. It can copy planned SQLite rows into a target adapter with explicit columns, preserve SQLite `rowid` as Postgres `entangled_rowid`, migrate support tables through the same planned path, reset identity columns, and return target counts plus semantic check statuses in the report model. No real Postgres or production target was touched.

## Done

- Extended `Entangled/packages/server-python/entangled/sql/migration.py` with source SELECT and target INSERT SQL builders.
- Added `execute_copy_plan` for explicit-column table copy.
- Added dynamic `rowid AS entangled_rowid` copy behavior.
- Added sequence reset SQL generation and execution for planned identity columns.
- Added target count, sync-version equality, transition count/max-ID, and rowid-copy checks.
- Added `execute_migration_plan` to run planned copies inside a target transaction and return a redacted `MigrationReport`.
- Tightened planner inventory to collect integer column max values so identity reset uses migrated column max values where appropriate.
- Added focused fake-adapter executor tests in `Entangled/packages/server-python/tests/test_migration_executor.py`.

## Verification

- `python -m pytest tests/test_migration_planner.py tests/test_migration_executor.py`: 10 passed.
- `python -m py_compile entangled/sql/migration.py`: passed.
- `python -m pytest`: 115 passed.

## Known Gaps

- This ticket does not expose a CLI; that remains assigned to `P055`.
- This ticket does not run against a real Postgres staging target; that remains assigned to `P050`.
- Fake-adapter tests prove SQL shape and report/check behavior, not psycopg type adaptation.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/migration.py`
- `Entangled/packages/server-python/tests/test_migration_executor.py`
