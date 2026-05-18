# PR-313 — Worker Lease FSM

Status: Closed

## Goal

Make worker claim, heartbeat, timeout, release, and reclaim behavior explicit
lease events instead of scattered direct SQL mutation.

## Scope

- Define lease FSM vocabulary.
- Route stale task and saga recovery through lease events.
- Keep heartbeat fields only as projections of lease state.
- Add watchdog tests proving it emits events rather than mutating lifecycle
  state directly.

## Explicit Dependency Boundary Review

Allowed explicit inputs:

- worker id
- machine id
- lease timeout cutoff computed by caller
- current timestamp supplied by caller

Forbidden hidden inputs:

- reducer-local time
- reducer-local DB queries

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- Direct task heartbeat SQL mutation in `TaskQueue.heartbeat`.
- Direct saga heartbeat SQL mutation in `SagaRepository.heartbeat`.
- Stale task/saga recovery ownership of claim expiration; recovery now records
  `lease_timed_out` before lifecycle projection.

## Verification

- `python -m py_compile queue_service/lease_fsm.py queue_service/lease_ledger.py queue_service/queue_db.py queue_service/saga_repo.py queue_service/db/schema.py`
- `pytest -q tests/test_pr313_worker_lease_fsm.py tests/test_pr313_worker_lease_ledger.py tests/test_pr313_worker_lease_cutover.py tests/test_pr307_taskqueue_old_sql_residue_cleanup.py tests/test_pr312_saga_old_sql_residue_cleanup.py tests/test_pr309_saga_fsm_store_ledger.py`
- `pytest -q tests/test_queue_explicit_dependencies.py tests/test_pr304_task_lifecycle_fsm.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_pr308_saga_lifecycle_fsm.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr311_saga_compensation_outbox_cutover.py`
- `pytest -q` under `novaic-agent-runtime` (`425 passed`)
- Residue scan confirms direct `UPDATE tq_tasks` and `UPDATE tq_sagas` remain
  only inside projection writers.

## Closure Notes

Closed. Added pure worker lease FSM, lease ledger tables/adapter, task and saga
lease event recording for acquire/heartbeat/release/timeout, and tests proving
heartbeat/recovery are lease-owned projections instead of direct lifecycle
mutation.
