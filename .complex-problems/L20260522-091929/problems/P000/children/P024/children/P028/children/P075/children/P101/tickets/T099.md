# Add Queue Migration Semantic Validation And Operator CLI

## Problem Definition

P099 and P100 provide planning and copy execution, but production use still needs semantic validation and an operator-facing command. The command must support dry-run planning, execution, validation, redacted JSON report writing, and safe handling of non-empty targets. Validation must compare row counts and Queue-specific aggregates so cutover does not restart on silently corrupted state.

## Proposed Solution

1. Extend `queue_service/db/migration.py` with semantic aggregate helpers:
   - per-table row count validation;
   - task/saga/session state histograms;
   - outbox status counts by table;
   - idempotency status counts;
   - worker lease state counts;
   - max event/outbox IDs;
   - config schema version.
2. Add `validate_queue_migration(...)` that compares source vs target aggregates and mutates/returns a `MigrationReport` with `status="validated"` or `status="error"`.
3. Add a CLI module, e.g. `queue_service/db/migrate_sqlite_to_postgres.py`, with `main(argv=None)`:
   - `--sqlite-path`;
   - `--postgres-dsn` or `--postgres-dsn-file`;
   - `--report-path`;
   - `--dry-run`;
   - `--allow-non-empty-target`;
   - injectable DB factories for tests if needed.
4. CLI dry-run runs planning and writes a redacted report without copying target rows.
5. CLI execution initializes schema, copies rows, validates semantics, writes report JSON, and returns non-zero on blocked/error status.

## Acceptance Criteria

- Semantic validation compares row counts for all active tables.
- Semantic aggregates include task/saga/session states, pending/dead-letter outbox counts, idempotency statuses, worker lease states, max event/outbox IDs, and config schema version.
- CLI argument parsing supports required source/target/report/dry-run/non-empty target options.
- Dry-run writes a redacted report and does not call copy execution.
- Execution path writes a redacted report after copy plus validation.
- Tests cover validation success, validation failure, dry-run/report writing, CLI argument handling, and execution report writing without a live Postgres server.

## Verification Plan

- Add `tests/test_queue_migration_validation_cli.py`.
- Run all migration tests, Queue Postgres boundary tests, and compile checks.

## Risks

- Max ID validation is mostly meaningful for integer row IDs, but this Queue schema uses text IDs for many event/outbox tables; validation should report a comparable max value per table without forcing integer semantics.
- CLI should not leak DSNs in exception paths or reports.

## Assumptions

- Live production invocation belongs to later staging/cutover tasks; P101 provides the command and deterministic tests.
- The CLI can use `create_queue_database(..., backend="postgres")` and SQLite connections in real use, while tests can inject fake DB factories through `main(...)` helpers or smaller command functions.
