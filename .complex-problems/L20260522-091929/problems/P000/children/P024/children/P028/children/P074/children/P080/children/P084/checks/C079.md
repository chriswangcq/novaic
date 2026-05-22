# Task Queue Postgres Query Dialect Verified

## Summary

P084 is successful. Result `R074` adds and wires backend-aware TaskQueue query helpers for claim candidates, stale recovery candidates, and cancel-by-agent filtering. The Postgres query forms use native timestamptz comparisons, JSONB predicates, stable ordering, and `FOR UPDATE ... SKIP LOCKED`, while sqlite forms remain covered for current fixtures.

## Evidence

- `novaic-agent-runtime/queue_service/queue_db.py` now has `_task_claim_candidate_sql`, `_task_recover_stale_candidate_sql`, `_task_cancel_query_sql`, and `_queue_backend_name`.
- `TaskQueue.claim`, `recover_stale`, and `cancel_all` call the helpers rather than hardcoding one SQLite SQL body.
- Postgres claim candidate SQL includes `ts.next_retry_at <= ?`, `jsonb_array_elements_text`, `COALESCE(ss.step_results, '{}'::jsonb) ? dep.step_name`, `ORDER BY t.created_at, t.id`, and `FOR UPDATE OF ts SKIP LOCKED`.
- Postgres stale recovery SQL includes `ls.heartbeat_at < ?`, `ORDER BY ls.heartbeat_at, ts.task_id`, and `FOR UPDATE OF ts, ls SKIP LOCKED`.
- Postgres cancel-by-agent filtering uses `t.payload ->> 'agent_id' = ?`.
- `QueuePostgresDatabase._convert_placeholders` preserves JSONB `?` operators with identifier right operands while still converting qmark placeholders.
- Verification passed with 61 selected Queue tests.

## Criteria Map

- Postgres task claim candidate SQL uses native timestamp comparisons without SQLite `datetime(...)` -> asserted in `tests/test_queue_postgres_task_query_dialect.py`.
- Postgres dependency readiness uses JSONB functions/operators instead of `json_each`/`json_extract` -> asserted in `tests/test_queue_postgres_task_query_dialect.py`.
- Postgres claim candidate SQL includes `FOR UPDATE SKIP LOCKED` -> asserted as `FOR UPDATE OF ts SKIP LOCKED`.
- Postgres stale recovery uses native lease heartbeat comparison without `datetime(...)` -> asserted in `tests/test_queue_postgres_task_query_dialect.py`.
- Postgres cancel-by-agent uses `payload ->> 'agent_id'` -> asserted in `tests/test_queue_postgres_task_query_dialect.py`.
- Focused unit tests assert Postgres and sqlite dialect outputs without production access -> 6 new task query dialect tests plus existing sqlite TaskQueue candidate tests passed.

## Execution Map

- T078 / R074 -> implemented query helpers, wiring, placeholder conversion refinement, tests, and verification.

## Stress Test

- Failure mode: JSONB dependency `? dep.step_name` is mistaken for a bind placeholder. Boundary tests now assert the adapter preserves this operator while converting ordinary placeholders.
- Failure mode: sqlite task candidate tests regress due helper extraction. Existing `test_pr316_taskqueue_state_candidate_cutover.py` and `test_queue_explicit_dependencies.py` still pass.
- Failure mode: Postgres SQL still contains SQLite `datetime`, `json_each`, or `json_extract`; focused tests assert those strings are absent from PG helper output.

## Residual Risk

- P084 only establishes candidate query dialect and partial wiring. Actual task mutation row locking/compare-update behavior remains P085, and idempotency ledger behavior remains P086. Real Postgres integration remains later.

## Result IDs

- R074
