# Queue Migration Planner Result

## Summary

Added the read-only Queue SQLite-to-Postgres migration planner/report foundation. It derives active table order from the schema contract, counts source/target rows, blocks non-empty targets by default, redacts DSN inputs, and emits a structured report with semantic aggregate placeholders for later validation work.

## Done

- Added `queue_service/db/migration.py`.
- Defined `QUEUE_MIGRATION_TABLES` from `QUEUE_TABLES` and exposed `queue_migration_table_plan()`.
- Added `MigrationReport`, `TableCountInspection`, and table plan dataclasses.
- Implemented `plan_queue_sqlite_to_postgres_migration(...)` as a read-only planner over source and target DB abstractions.
- Added DSN and DSN-file redaction helpers.
- Added semantic aggregate placeholders for P101 validation.
- Added `tests/test_queue_migration_planner.py` covering table order, source/target counts, non-empty target blocking, explicit override, count errors, JSON report output, and redaction.

## Verification

- `pytest tests/test_queue_migration_planner.py tests/test_queue_postgres_boundary.py tests/test_queue_runtime_postgres_default.py` passed: 20 tests.
- `python -m compileall queue_service/db/migration.py tests/test_queue_migration_planner.py` passed.

## Known Gaps

- No copy execution is implemented in P099; P100 owns data copy and JSON conversion.
- No CLI or final semantic validation is implemented in P099; P101 owns operator entrypoint and invariant checks.

## Artifacts

- `novaic-agent-runtime/queue_service/db/migration.py`
- `novaic-agent-runtime/tests/test_queue_migration_planner.py`
