# PR-316 TaskQueue State Candidate Cutover

Status: Closed
Owner: Codex
Phase: 7

## Goal

Make TaskQueue lifecycle candidate selection use the task FSM state and worker
lease FSM state instead of `tq_tasks` projection status/heartbeat columns.

## Scope

- `novaic-agent-runtime/queue_service/queue_db.py`
- TaskQueue claim, stale recovery, cancel-all, and topic listing queries.
- Targeted tests proving candidate queries do not read projection lifecycle
  status as authority.

## Deletion Scope

- Remove active candidate selectors of the form `FROM tq_tasks WHERE status...`.
- Remove active stale selectors that decide timeout from `tq_tasks.heartbeat_at`.

## Acceptance Criteria

- `claim()` selects pending candidates from `tq_task_state`.
- Saga dependency checks read saga step results from `tq_saga_state`.
- `recover_stale()` selects claimed candidates by joining task state to active
  worker lease state and comparing lease heartbeat.
- `cancel_all()` selects cancellable tasks from `tq_task_state`.
- `get_topics()` reads known topics from `tq_task_state`.
- Existing TaskQueue behavior tests still pass.

## Verification

- Targeted PR-316 tests.
- Existing PR-306/307/313/315 tests.
- Full `novaic-agent-runtime` test suite if runtime changes are stable.

## Closure Notes

- `TaskQueue.claim()` now selects candidates from `tq_task_state`, joins
  `tq_tasks` only for task content, and reads saga dependency results from
  `tq_saga_state`.
- `TaskQueue.recover_stale()` now selects stale claimed tasks from task state
  joined to `tq_worker_lease_state`.
- `TaskQueue.cancel_all()`, `get_topics()`, and `count_by_status()` now read
  lifecycle candidates and counts from `tq_task_state`.
- Task projection writes no longer use projection `status` as CAS authority.
- Task reducer inputs now hydrate status, generation, retry counts, and claim
  ownership from the task FSM state row.
- Cancelling a claimed task through `cancel_all()` now records a lease release,
  so the task lifecycle and worker lease lifecycle close together.
- Verification: `tests/test_pr316_taskqueue_state_candidate_cutover.py`,
  PR-306/307/313/315 regression tests, and full runtime suite passed.
