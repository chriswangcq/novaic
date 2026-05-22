# Add Queue Migration CLI And Report Writing

## Problem Definition

Queue migration now has planning, copy execution, and semantic validation library functions, but operators still need a safe command. The CLI must support dry-run preflight, execution plus validation, redacted JSON report writing, and non-zero exits for blocked/error outcomes without requiring tests to hit a live Postgres server.

## Proposed Solution

1. Add `queue_service/db/migrate_sqlite_to_postgres.py`.
2. Provide `build_parser()` and `main(argv=None, db_factory=None)` for testable CLI invocation.
3. CLI options:
   - `--sqlite-path`;
   - `--postgres-dsn`;
   - `--postgres-dsn-file`;
   - `--report-path`;
   - `--dry-run`;
   - `--allow-non-empty-target`.
4. Real DB factory:
   - opens SQLite with `sqlite3.connect`;
   - creates Postgres target with `create_queue_database(backend="postgres", ...)`;
   - connects/initializes target schema when executing copy;
   - closes both DBs where possible.
5. Dry-run path calls planner and writes report JSON, without copy or validation.
6. Execution path calls copy execution, semantic validation, writes report JSON, and exits `0` only for validated/copied/ready success statuses as appropriate.
7. Add tests with injected fake DB factories for argument handling, dry-run report writing, execution report writing, and error status exit.

## Acceptance Criteria

- Module entrypoint exists and can be run via `python -m queue_service.db.migrate_sqlite_to_postgres`.
- CLI exposes required options and enforces either DSN or DSN file.
- Dry-run writes a redacted report and does not call copy execution.
- Execution path initializes/copies/validates and writes final redacted report.
- CLI returns non-zero for blocked/error report statuses.
- Tests cover dry-run, execution, argument validation, report redaction, and error exit without live Postgres.

## Verification Plan

- Add `tests/test_queue_migration_cli.py`.
- Run all migration tests, Queue Postgres boundary tests, and compile checks.

## Risks

- Avoid accidental DSN leakage in stdout/stderr or report JSON.
- Real DB factory must not mutate target in dry-run mode.

## Assumptions

- Production execution of this CLI belongs to later staging/cutover ledger tasks.
