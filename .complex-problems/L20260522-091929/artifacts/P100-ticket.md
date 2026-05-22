# Implement Queue Migration Copy Execution

## Problem Definition

P099 provides read-only planning/reporting, but no rows are copied. P100 must add reusable copy execution that initializes/verifies the Postgres schema, refuses unsafe non-clean targets by default, copies all active Queue tables in plan order, preserves identities, and converts SQLite JSON text columns into native JSON-compatible values for Postgres JSONB binding.

## Proposed Solution

1. Extend `queue_service/db/migration.py` with copy execution helpers:
   - JSON column metadata per active table;
   - column discovery for SQLite source rows;
   - `copy_queue_sqlite_to_postgres(...)` that calls the planner, requires `ready` status unless explicitly allowed, optionally initializes target schema, copies table rows, then returns a report.
2. Keep DB I/O generic:
   - source uses SQLite-style `execute`;
   - target uses the existing Queue Postgres DB surface (`execute`, `executemany`, optional `commit`);
   - no direct psycopg dependency in migration logic.
3. Preserve all source values except JSON columns, which are decoded from SQLite text into dict/list/scalar values before binding.
4. Fail safely:
   - malformed JSON produces an `error` report and no silent coercion;
   - non-empty target without override remains blocked;
   - target insert failures are reported.
5. Add fixture/fake tests for representative task, saga, session, worker lease, outbox, idempotency, and config rows.

## Acceptance Criteria

- Copy execution can copy every `QUEUE_MIGRATION_TABLES` table plus `config` from SQLite source into a target abstraction.
- Target schema initialization hook is invoked before copy when provided.
- Non-empty target is refused by default.
- JSON text columns are decoded into native Python values for Postgres binding.
- Primary/event/outbox IDs, natural IDs, generations, timestamps, and status fields are preserved in bound rows.
- Malformed JSON or insert failure produces a structured error report.
- Tests cover successful representative copy, non-empty target refusal, malformed JSON, and schema initialization.

## Verification Plan

- Extend `tests/test_queue_migration_planner.py` or add `tests/test_queue_migration_copy.py`.
- Run migration tests, Queue Postgres boundary tests, and compile checks.

## Risks

- Current schema creation may create many columns; tests should use current schema helpers or table column discovery rather than hand-maintaining column lists.
- Copy order must remain schema-derived to avoid stale migration drift.

## Assumptions

- P100 does not own CLI argument parsing or final semantic aggregate validation; P101 owns those.
- The target is a clean Postgres Queue database or an explicit fake target in tests.
