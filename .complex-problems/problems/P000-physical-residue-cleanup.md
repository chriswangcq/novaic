# P000: Physical Residue Cleanup After Generic Worker Substrate Migration

Status: done
Parent: none
Ticket: T000

## Problem

The generic worker substrate migration is functionally complete, but the
deletion count is low because old module-local launch helpers, stale comments,
and unused compatibility parameters still remain. These residues can mislead
future agents into copying old worker entrypoints or believing gateway/broadcast
dependencies still exist in task/saga/scheduler worker business classes.

## Success Criteria

- Remove unused worker module launch helpers and direct `__main__` entrypoints
  that duplicate `main_novaic.py`.
- Remove unused `gateway_url` constructor plumbing from migrated worker classes
  where no computation reads it.
- Keep deploy/start paths working by updating active scripts or preserving only
  intentionally accepted CLI compatibility.
- Keep runtime tests passing.
- Add or update residue guards so the removed shapes do not return.

## Subproblems

- None initially; execute directly unless success review finds a gap.

## Results

- Deleted retired `main_task.py` and `main_saga.py` standalone worker entrypoints.
- Moved Saga worker assembly into `main_novaic.py` so the unified runtime
  entrypoint owns the process boundary.
- Removed unused worker `gateway_url` constructor/CLI plumbing and stale
  module-local launch helpers from migrated workers.
- Updated active root/app start scripts and packaging hints to match the
  unified worker modes.

## Check

- `python -m compileall -q main_novaic.py task_queue/workers tests/test_pr335_worker_residue_guards.py`
- `pytest -q tests/test_pr335_worker_residue_guards.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr328_health_generic_worker.py`
- `pytest -q` in `novaic-agent-runtime` -> 487 passed.
- `bash -n scripts/start.sh`
- `bash -n novaic-app/scripts/start-backends.sh`
- `python scripts/ci/check_start_config_contract.py`
- `pytest -q scripts/ci/test_no_legacy_file_hot_paths.py`

## Follow-ups

- Local app backend service graph still deserves a separate product-level audit
  because this cleanup only removed invalid worker invocations and flags. The
  broader local script still has fewer service sections than production
  `scripts/start.sh`; that is not a worker substrate residue but should be
  checked before relying on it for full local E2E.
