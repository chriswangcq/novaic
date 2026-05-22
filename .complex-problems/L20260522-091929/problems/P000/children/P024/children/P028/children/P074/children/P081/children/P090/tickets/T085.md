# Add Saga Postgres Candidate Query Dialect

## Problem Definition

Saga claim, stale recovery, and cancel-by-agent candidate queries still embed SQLite-specific SQL in `queue_service/saga_repo.py`. Postgres mode needs native timestamptz comparisons, JSONB context predicates, stable ordering, and explicit row locking for candidate selection.

## Proposed Solution

Add backend-aware helper functions in `saga_repo.py` for saga claim candidates, stale recovery candidates, and cancel candidates. Wire `SagaRepository.claim`, `recover_stale`, and `cancel_all` through those helpers. The Postgres helpers should use `FOR UPDATE ... SKIP LOCKED`, avoid SQLite `datetime(...)`, and use `ss.context ->> 'agent_id' = ?` for cancel-by-agent filtering. Keep sqlite helper output behavior-compatible with the existing SQL.

## Acceptance Criteria

- Postgres claim candidate SQL locks `tq_saga_state` rows with `FOR UPDATE OF ss SKIP LOCKED`.
- Postgres claim ordering is stable by saga creation time and id.
- Postgres stale recovery uses native heartbeat comparison and locks saga state plus lease state rows.
- Postgres cancel-by-agent uses JSONB scalar extraction instead of `json_extract`.
- SQLite helper SQL keeps `datetime(...)` and `json_extract` behavior where applicable.
- `claim`, `recover_stale`, and `cancel_all` call the backend-aware helpers.

## Verification Plan

Add focused tests for saga Postgres and sqlite helper SQL shapes, including absence of `datetime(...)` and `json_extract` in Postgres helpers. Add fake Postgres repository no-op tests to assert `claim`, `recover_stale`, and `cancel_all` use the expected lock clauses. Run these new tests plus existing saga FSM/lease tests and the current Queue Postgres boundary/idempotency tests.

## Risks

- Query helper extraction could regress sqlite saga candidate behavior.
- `FOR UPDATE` placement must be valid for the selected joins and limits.
- Real Postgres contention behavior remains a later staging validation item.

## Assumptions

- Single-row saga mutation locking is handled by P091.
- Worker lease ledger write semantics are handled by P092.
