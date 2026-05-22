# Queue Postgres JSON Expression Indexes Verified

## Summary

P078 is successful. Result `R072` added the two required Queue Postgres JSONB expression indexes, protected the adapter from converting JSONB `?` operators into bind placeholders, and verified the behavior with focused tests.

## Evidence

- `novaic-agent-runtime/queue_service/db/schema.py` includes `idx_tq_tasks_payload_agent` with `tq_tasks ((payload ->> 'agent_id')) WHERE payload ? 'agent_id'`.
- `novaic-agent-runtime/queue_service/db/schema.py` includes `idx_tq_saga_state_context_agent` with `tq_saga_state ((context ->> 'agent_id')) WHERE context ? 'agent_id'`.
- `novaic-agent-runtime/queue_service/db/postgres.py` preserves JSONB question operators in placeholder conversion.
- `novaic-agent-runtime/tests/test_queue_postgres_boundary.py` asserts both expression indexes and schema execution through the adapter.
- Focused verification passed: 11 Queue Postgres boundary tests and 35 selected Queue schema/ledger tests.

## Criteria Map

- `idx_tq_tasks_payload_agent` exists with required expression and predicate -> covered by schema diff and `tests/test_queue_postgres_boundary.py`.
- `idx_tq_saga_state_context_agent` exists with required expression and predicate -> covered by schema diff and `tests/test_queue_postgres_boundary.py`.
- Focused tests assert both JSON expression indexes and still pass -> `tests/test_queue_postgres_boundary.py` passed with 11 tests; selected Queue suite passed with 35 tests.

## Execution Map

- T074 / R072 -> added the missing schema statements, adapter conversion protection, and tests; no spawned child was needed.

## Stress Test

- Failure mode: the schema DDL contains Postgres JSONB `?` operators, but the DB adapter mistakenly treats them as qmark bind placeholders. This is covered by `test_init_postgres_schema_preserves_jsonb_question_operator_through_adapter`, which verifies that schema execution preserves `payload ? 'agent_id'` and `context ? 'agent_id'` while still converting `VALUES (?, ?)` to psycopg placeholders.

## Residual Risk

- No blocking residual risk for P078. Real Postgres execution remains a later staging/cutover concern, but the required schema text and adapter boundary behavior are unit-verified.

## Result IDs

- R072
