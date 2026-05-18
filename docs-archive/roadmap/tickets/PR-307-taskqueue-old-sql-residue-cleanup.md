# PR-307 — TaskQueue Old SQL Residue Cleanup

Status: Closed

## Goal

Delete old imperative task lifecycle branches after `TaskQueue` is cut over to
the task FSM.

## Scope

- Remove direct status decision SQL from task lifecycle methods.
- Remove stale tests that assert old mutation paths.
- Add guard tests that fail on reintroduced active direct status branches.

## Explicit Dependency Boundary Review

No business decision may be encoded in SQL text. SQL can persist reducer
decisions and projections only.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- Direct task lifecycle status decision branches.
- Old compatibility tests and comments for imperative task status transitions.

## Verification

- Runtime task queue suite.
- Residue grep for `UPDATE tq_tasks SET status` in active decision methods.
- `git diff --check`.

## Closure Notes

Closed on 2026-05-07.

- Added a single `TaskQueue._apply_task_projection(...)` writer for task
  lifecycle projection columns.
- Removed direct lifecycle `UPDATE tq_tasks SET status ...` SQL from `claim`,
  `complete`, `fail`, `recover_stale`, `release_task`, and `cancel_all`.
- Added a static residue guard proving active lifecycle methods do not embed
  `UPDATE tq_tasks` or `SET status` SQL and must route projection writes
  through `_apply_task_projection(...)`.
- Verification:
  - `python -m py_compile queue_service/queue_db.py queue_service/task_fsm.py queue_service/task_ledger.py`
  - `pytest tests/test_pr307_taskqueue_old_sql_residue_cleanup.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_pr304_task_lifecycle_fsm.py tests/test_pr305_task_fsm_store_ledger.py`
  - `pytest tests/unit/task_queue tests/test_pr307_taskqueue_old_sql_residue_cleanup.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_queue_explicit_dependencies.py tests/integration/test_saga_dag_refactor.py`
