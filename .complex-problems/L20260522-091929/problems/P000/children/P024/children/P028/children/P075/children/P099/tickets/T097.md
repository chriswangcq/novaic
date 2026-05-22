# Build Queue Migration Planner And Report Foundation

## Problem Definition

The Queue SQLite-to-Postgres migration needs a deterministic planning/reporting layer before data copy. The planner must know the active table order, inspect source and target row counts, detect unsafe non-empty targets, and emit a redacted structured report suitable for production ledger evidence.

## Proposed Solution

1. Add `queue_service/db/migration.py` with:
   - `QUEUE_MIGRATION_TABLES` derived from `queue_service.db.schema.QUEUE_TABLES`;
   - dataclasses for table counts, target preflight, report metadata, and migration report;
   - `redact_dsn(...)` / `redact_path(...)` helpers;
   - source/target row-count inspection helpers that use the existing DB surface (`execute`, cursor `fetchone`, cursor `close` when available).
2. Implement a planner function that:
   - counts every active table in the SQLite source and target abstraction;
   - marks target cleanliness;
   - records non-empty target table errors unless explicitly allowed;
   - initializes semantic aggregate placeholders for later P101 validation.
3. Keep this child read-only: no data copying, truncation, or mutation.
4. Add tests with in-memory SQLite and fake target DB objects.

## Acceptance Criteria

- Active migration table order is imported from the current schema contract and includes `config`.
- Planner returns source and target row counts for every active table.
- Planner marks a non-empty target unsafe by default and produces table-specific errors.
- Report output redacts inline DSNs and DSN file paths.
- Report schema includes status, table counts, semantic aggregate placeholders, errors, and elapsed/timestamp metadata.
- Tests cover empty target, non-empty target, missing table handling where appropriate, and redaction.

## Verification Plan

- Add `tests/test_queue_migration_planner.py`.
- Run planner tests, Queue Postgres boundary/schema tests, and compile checks for the new module.

## Risks

- Counting missing target tables before schema initialization could blur planner vs execution responsibilities; the planner should report missing counts/errors without creating schema.
- Redaction must be conservative: never echo passwords or full DSN file paths in report JSON.

## Assumptions

- P099 does not copy data; P100 owns copy execution and JSON conversion.
- P101 owns CLI and final semantic aggregate validation; P099 only creates placeholders and report shape.
