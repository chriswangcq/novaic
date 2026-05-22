# Queue Postgres Boundary Needs JSON Expression Index Follow-Up

## Summary

Result `R071` completes most of the Queue Postgres boundary: backend selection, DSN/DSN-file handling, Postgres adapter behavior, full table coverage, JSONB/timestamptz column choices, safe health/readiness reporting, and focused tests. However, the original P073 success criteria explicitly require JSON expression indexes, and the P017 design artifact requires two first-cutover expression indexes that are not present in the new Postgres schema. P073 should not be marked successful until those indexes and assertions are added.

## Blocking Gaps

- Missing required JSONB expression indexes from `.complex-problems/L20260522-091929/artifacts/queue-pg-jsonb-time-index-sqlite-assumptions.md`: `idx_tq_tasks_payload_agent` on `tq_tasks ((payload ->> 'agent_id')) WHERE payload ? 'agent_id'`, and `idx_tq_saga_state_context_agent` on `tq_saga_state ((context ->> 'agent_id')) WHERE context ? 'agent_id'`.

## Result IDs

- R071
