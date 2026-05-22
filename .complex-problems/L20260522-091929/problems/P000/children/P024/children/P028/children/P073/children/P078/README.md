# Add Queue Postgres JSON Expression Indexes

## Problem

P073 added the Queue Postgres schema and database boundary, but the schema is missing the two required JSONB expression indexes from the Queue PG design artifacts. Without them, the schema does not fully satisfy the original index-family success criteria for first-cutover Postgres behavior.

## Success Criteria

- `POSTGRES_SCHEMA_STATEMENTS` includes `idx_tq_tasks_payload_agent` on `tq_tasks ((payload ->> 'agent_id')) WHERE payload ? 'agent_id'`.
- `POSTGRES_SCHEMA_STATEMENTS` includes `idx_tq_saga_state_context_agent` on `tq_saga_state ((context ->> 'agent_id')) WHERE context ? 'agent_id'`.
- Focused tests assert both JSON expression indexes and still pass with the existing Queue Postgres boundary test suite.
