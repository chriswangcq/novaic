# Saga Query Dialect Verified

## Summary

P090 is successful. Result `R081` adds and wires backend-aware saga candidate SQL for claim, stale recovery, and cancel-by-agent paths. The Postgres helpers use stable ordering, native timestamp comparison, JSONB context filtering, and `FOR UPDATE ... SKIP LOCKED`; sqlite helper SQL keeps existing behavior.

## Evidence

- `saga_repo.py` now has `_saga_claim_candidate_sql`, `_saga_recover_stale_candidate_sql`, `_saga_cancel_query_sql`, and `_saga_backend_name`.
- `SagaRepository.claim`, `recover_stale`, and `cancel_all` call the helpers.
- Postgres claim SQL includes `ORDER BY s.created_at, s.id` and `FOR UPDATE OF ss SKIP LOCKED`.
- Postgres recovery SQL includes `ls.heartbeat_at < ?`, `ORDER BY ls.heartbeat_at NULLS FIRST, ss.saga_id`, and `FOR UPDATE OF ss, ls SKIP LOCKED`.
- Postgres cancel-by-agent SQL uses `ss.context ->> 'agent_id' = ?`.
- Focused verification passed with 9 saga query dialect tests and 59 selected saga/lease/Queue regression tests.

## Criteria Map

- Postgres claim candidate SQL uses stable ordering and locks saga-state rows -> focused claim SQL test and no-op repository test.
- Postgres stale recovery uses native heartbeat comparison and locks saga plus lease state rows -> focused recovery SQL test and no-op repository test.
- Postgres cancel-by-agent uses JSONB context predicates -> focused cancel SQL test and no-op repository test.
- SQLite claim/recovery/cancel behavior remains covered -> sqlite helper shape tests plus selected existing saga tests passed.
- Focused tests assert Postgres SQL shape and absence of SQLite-only `datetime(...)`/`json_extract` in Postgres helpers -> `tests/test_queue_postgres_saga_query_dialect.py`.

## Execution Map

- T085 / R081 -> implemented saga query helpers, wiring, tests, and verification.

## Stress Test

- Failure mode: Postgres recovery still uses SQLite `datetime(...)`. Covered by absence assertion and native heartbeat comparison test.
- Failure mode: cancel-by-agent still uses `json_extract`. Covered by JSONB operator assertion.
- Failure mode: candidate selection can race without row locks. Covered by `FOR UPDATE ... SKIP LOCKED` assertions.
- Failure mode: sqlite query shape regresses. Covered by sqlite helper tests and selected saga regression tests.

## Residual Risk

- Saga single-row lifecycle mutation locking remains P091.
- Worker lease ledger Postgres semantics remain P092.
- Live Postgres contention validation remains a later staging problem.

## Result IDs

- R081
