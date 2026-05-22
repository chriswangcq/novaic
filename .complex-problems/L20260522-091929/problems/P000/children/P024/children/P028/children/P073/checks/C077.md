# Queue Postgres Schema And Boundary Verified

## Summary

P073 is successful after follow-up `P078`. Results `R071` and `R072` together implement and verify the Queue Postgres schema/database boundary: explicit backend selection, safe DSN/DSN-file handling, Queue-owned Postgres adapter, full active table coverage, required JSONB/timestamptz choices, primary/unique/partial/candidate/expression indexes, transaction/advisory-lock behavior, and focused tests without production access.

## Evidence

- `novaic-agent-runtime/queue_service/db/postgres.py` adds `QueuePostgresDatabase` with DSN/DSN-file connect paths, psycopg placeholder conversion, percent escaping, SQLite-like row access, advisory locks, and transaction helpers.
- `novaic-agent-runtime/queue_service/db/schema.py` adds `POSTGRES_SCHEMA_STATEMENTS`, `POSTGRES_SCHEMA_SQL`, `QUEUE_TABLES`, and `init_postgres_schema` for config plus all active Queue tables.
- `novaic-agent-runtime/queue_service/db/schema.py` uses `jsonb` for durable JSON fields and `timestamptz` for Queue timestamp fields.
- `novaic-agent-runtime/queue_service/db/schema.py` includes required primary keys, unique idempotency constraints, partial pending outbox indexes, candidate indexes, idempotency lease index, and the two required JSONB expression indexes from P078.
- `novaic-agent-runtime/main_novaic.py` and `novaic-agent-runtime/queue_service/main.py` add explicit sqlite/postgres runtime configuration and safe health/root/readiness backend reporting.
- `novaic-agent-runtime/tests/test_queue_postgres_boundary.py` verifies schema coverage, DSN/DSN-file behavior, direct DSN secrecy in public info, placeholder conversion, JSONB question-operator preservation, transactions, advisory locks, and schema initialization without production access.
- Verification passed: 35 selected Queue schema/ledger tests after P078, plus compile and diff checks.

## Criteria Map

- Queue Postgres schema exists for all active task, saga, session, worker lease, outbox, config, and idempotency tables -> `QUEUE_TABLES` and `POSTGRES_SCHEMA_STATEMENTS` cover `config` and every active `tq_*` table; tested in `test_postgres_schema_covers_queue_tables_indexes_and_types`.
- JSON columns use JSONB and timestamp columns use timestamptz -> schema DDL and boundary tests assert representative `jsonb` and `timestamptz` fields.
- Primary keys, unique idempotency constraints, partial indexes, candidate indexes, and JSON expression indexes are represented -> R071 added baseline keys/index families; R072 added and tested `idx_tq_tasks_payload_agent` and `idx_tq_saga_state_context_agent`.
- Queue runtime can be configured explicitly for `sqlite` or `postgres` -> `create_queue_database`, `NOVAIC_QUEUE_DB_BACKEND`, and `main_novaic.py queue-service --db-backend` cover explicit backend selection.
- Unit tests verify schema generation/initialization and database-boundary transaction behavior without touching production -> 35 selected tests passed, including fake-pool Postgres boundary tests.

## Execution Map

- T073 / R071 -> implemented the initial Queue Postgres boundary, schema baseline, runtime config, health/readiness reporting, requirements update, and focused tests.
- P078 / T074 / R072 -> closed the missing JSONB expression index gap and added adapter protection for JSONB `?` operators.

## Stress Test

- Failure mode: the schema looks complete but omits required JSONB expression indexes from the design artifact. This was caught by C075 and closed by P078/R072.
- Failure mode: Postgres JSONB `?` operators in DDL are accidentally converted to psycopg `%s` placeholders. R072 adds `test_init_postgres_schema_preserves_jsonb_question_operator_through_adapter`, proving DDL execution preserves the operator while ordinary bind placeholders still convert.
- Failure mode: adding PG support breaks default sqlite Queue tests. The selected existing Queue sqlite/schema/ledger tests still pass.

## Residual Risk

- Repository-level SQL still contains SQLite-specific expressions and is intentionally left for the next Queue cutover child. This is non-blocking for P073 because P073's scope is the schema/database boundary, not full repository porting or production cutover.
- Real Postgres integration and production cutover are still pending later children, so this check should not be read as Queue service production readiness on Postgres.

## Result IDs

- R071
- R072
