# Entangled Migration CLI Entry Point Result

## Summary

`T049` added a safe Entangled migration CLI entry point and command-level tests. Operators now have `entangled-migrate-postgres` for dry-run planning/report generation and non-dry-run execution wiring through `PostgresDatabase`, with DSN/DSN-file support, explicit target confirmation, redacted JSON reports, and local tests proving secret-safe behavior.

## Done

- Added `Entangled/packages/server-python/entangled/sql/migration_cli.py`.
- Added `[project.scripts]` entry point `entangled-migrate-postgres`.
- Added CLI flags for SQLite source, report path, target label, DSN or DSN file, clean-target confirmation, and dry-run.
- Implemented dry-run planning reports without opening Postgres connections.
- Implemented non-dry-run wiring through `PostgresDatabase.connect()`, `execute_migration_plan`, and `close()`.
- Added JSON report writing with redacted connection label usage.
- Added safe error handling that redacts common secret forms before stderr output.
- Added command tests in `Entangled/packages/server-python/tests/test_migration_cli.py`.

## Verification

- `python -m pytest tests/test_migration_planner.py tests/test_migration_executor.py tests/test_migration_cli.py`: 14 passed.
- `python -m py_compile entangled/sql/migration.py entangled/sql/migration_cli.py`: passed.
- `python -m pytest`: 119 passed.

## Known Gaps

- This ticket does not perform real staging migration; `P050` owns execution against a safe target.
- This ticket wires target cleanup confirmation, but actual target-clean implementation remains part of the execution/staging path before production cutover.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/migration_cli.py`
- `Entangled/packages/server-python/tests/test_migration_cli.py`
- `Entangled/packages/server-python/pyproject.toml`
