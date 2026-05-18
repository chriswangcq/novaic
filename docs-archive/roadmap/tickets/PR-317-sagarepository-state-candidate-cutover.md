# PR-317 SagaRepository State Candidate Cutover

Status: Closed
Owner: Codex
Phase: 7

## Goal

Make SagaRepository lifecycle candidate selection use saga/task FSM state and
worker lease FSM state instead of `tq_sagas` / `tq_tasks` projection lifecycle
columns.

## Scope

- `novaic-agent-runtime/queue_service/saga_repo.py`
- Saga claim, stale recovery, pending listing, cancel-all, and completion
  checks.
- Targeted tests proving projection lifecycle selectors are gone.

## Deletion Scope

- Remove active candidate selectors of the form `FROM tq_sagas WHERE status...`.
- Remove stale recovery selectors that decide timeout from
  `tq_sagas.heartbeat_at`.
- Remove saga completion checks based on `tq_tasks.status = 'done'`.

## Acceptance Criteria

- `claim()` selects pending sagas from `tq_saga_state`.
- `recover_stale()` selects running sagas by joining saga state to active worker
  lease state and comparing lease heartbeat.
- `get_pending()` and `cancel_all()` select from `tq_saga_state`.
- `check_saga_complete()` counts done task FSM state rows.
- Existing SagaRepository behavior tests still pass.

## Verification

- Targeted PR-317 tests.
- Existing PR-310/312/313/315 tests.
- Full `novaic-agent-runtime` test suite if runtime changes are stable.

## Closure Notes

- `SagaRepository.claim()` now selects pending sagas from `tq_saga_state`.
- `SagaRepository.recover_stale()` now selects running stale sagas from saga
  state joined to `tq_worker_lease_state`.
- `get_pending()` and `cancel_all()` now use `tq_saga_state` as the lifecycle
  candidate source.
- `check_saga_complete()` now counts completed child tasks from
  `tq_task_state`, not `tq_tasks.status`.
- Saga projection writes no longer use projection `status` as CAS authority.
- Saga reducer inputs now hydrate status, generation, context, step results,
  and claim ownership from the saga FSM state row.
- Verification: `tests/test_pr317_sagarepository_state_candidate_cutover.py`,
  PR-310/312/313/315 regression tests, and full runtime suite passed.
