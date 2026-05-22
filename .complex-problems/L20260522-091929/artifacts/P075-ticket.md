# Build Queue SQLite To Postgres Migration Tooling

## Problem Definition

Production Queue state still exists in SQLite `queue.db`. Before a safe Postgres cutover, we need deterministic tooling that copies all active Queue tables into a clean `novaic_queue` Postgres target, converts JSON/time values correctly, preserves identities, and emits a redacted report with row-count and semantic validation.

## Proposed Solution

Build the migration as a deliberate command/module rather than an ad hoc script:

1. Add a Queue migration package, e.g. `queue_service/db/migration.py`, that defines the table plan from `QUEUE_POSTGRES_TABLES`.
2. Add a CLI entrypoint, e.g. `python -m queue_service.db.migrate_sqlite_to_postgres`, accepting:
   - `--sqlite-path`;
   - `--postgres-dsn` or `--postgres-dsn-file`;
   - `--report-path`;
   - `--dry-run`;
   - an explicit `--allow-non-empty-target` override if we choose to support non-clean targets.
3. Implement planner/reporting first:
   - active table inventory;
   - source/target row counts;
   - DSN redaction;
   - semantic aggregate plan.
4. Implement copy execution:
   - initialize Postgres schema before copy;
   - require a clean target by default;
   - copy tables in dependency-safe order;
   - preserve integer event/outbox IDs and natural IDs;
   - convert SQLite JSON text columns into native JSONB-compatible values for Postgres binding.
5. Implement semantic validation:
   - row counts for every active Queue table;
   - task/saga/session state histograms;
   - pending/dead-letter outbox counts;
   - idempotency status counts;
   - worker lease state counts;
   - max event/outbox IDs;
   - config schema version.
6. Add fixture-driven tests for planner/report redaction, copy behavior, JSON/time conversion, and semantic validation failure cases.

## Acceptance Criteria

- A migration command can read a SQLite Queue DB and write all active tables into a clean Postgres target abstraction.
- Migration refuses a non-empty Postgres target by default.
- JSON columns are decoded from SQLite text and written as native dict/list-compatible values for Postgres JSONB binding.
- Row-count and semantic aggregate validation is reported for every active Queue table.
- Reports redact DSNs/secrets and include enough production evidence for ledger artifacts.
- Tests cover dry-run/planning, copy execution with representative fixture data, validation success/failure, and report redaction.

## Verification Plan

- Add unit tests using fake Postgres DB/cursor objects to verify copy SQL, bound values, clean-target checks, and report redaction without requiring a live Postgres instance.
- Add SQLite fixture tests that create representative Queue rows through existing schema/repository helpers where practical.
- Run migration tests, Queue Postgres schema/boundary tests, and compile checks.
- If the implementation discovers live-driver behavior that cannot be simulated safely, record it as a follow-up for staging validation rather than hiding it in unit tests.

## Risks

- Full data migration touches many tables; this likely benefits from split children if classification judges planner/reporting, copy execution, and semantic validation as independent subproblems.
- Postgres placeholder conversion and JSONB binding should reuse existing `QueuePostgresDatabase` behavior rather than inventing another SQL adapter.
- Cleaning a target database is dangerous; the default should refuse non-empty targets instead of truncating unless an explicit, tested flag is added later.

## Assumptions

- P075 builds deterministic migration tooling and tests; live production execution belongs to later staging/cutover problems.
- The target Postgres schema is the current Queue schema from `init_postgres_schema`.
- Active Queue tables are exactly the ordered list in `QUEUE_POSTGRES_TABLES` plus `config`.
