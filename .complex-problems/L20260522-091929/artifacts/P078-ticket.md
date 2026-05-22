# Add Queue Postgres Required JSONB Expression Indexes

## Problem Definition

The Queue Postgres schema added in P073 covers the active tables and most index families, but it omits the two required JSONB expression indexes identified in the Queue Postgres design artifacts. P073 cannot close until those indexes are represented and tested.

## Proposed Solution

Add the two required `CREATE INDEX IF NOT EXISTS` statements to `POSTGRES_SCHEMA_STATEMENTS` in `queue_service/db/schema.py`: one for `tq_tasks ((payload ->> 'agent_id')) WHERE payload ? 'agent_id'`, and one for `tq_saga_state ((context ->> 'agent_id')) WHERE context ? 'agent_id'`. Extend the focused Queue Postgres boundary test to assert both index names and expressions.

## Acceptance Criteria

- `idx_tq_tasks_payload_agent` exists in Queue Postgres schema SQL with the required `payload ->> 'agent_id'` expression and `payload ? 'agent_id'` predicate.
- `idx_tq_saga_state_context_agent` exists in Queue Postgres schema SQL with the required `context ->> 'agent_id'` expression and `context ? 'agent_id'` predicate.
- Existing Queue Postgres boundary tests pass.

## Verification Plan

Run `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py` from `novaic-agent-runtime`; optionally rerun the same focused Queue schema/ledger tests used in P073 if the diff touches surrounding schema code.

## Risks

- PostgreSQL treats `?` as a JSONB operator, while the adapter also converts qmark placeholders; these DDL statements are executed through the schema initializer and must preserve the literal JSONB operator in statement text.
- Tests must assert the expression text clearly enough to catch accidental omission without depending on formatting trivia.

## Assumptions

- The two expression indexes are required for first-cutover readiness per the P017 design artifact.
- No repository SQL porting or production Postgres execution is needed for this follow-up.
