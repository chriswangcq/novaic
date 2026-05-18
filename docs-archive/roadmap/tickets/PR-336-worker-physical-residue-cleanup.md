# PR-336 Worker Physical Residue Cleanup

Status: Closed
Phase: 7
Owner: Codex

## Goal

Finish the physical cleanup after the generic worker substrate cutover. The
system should not keep retired worker entrypoints or compatibility arguments
that imply old lifecycle ownership still exists.

## Scope

- Delete retired standalone Agent Runtime worker entrypoints.
- Inline Saga worker assembly into `main_novaic.py`.
- Remove worker-local launch helpers and direct `__main__` blocks from migrated
  worker modules.
- Remove unused worker `gateway_url` constructor/CLI plumbing from task, saga,
  scheduler, and health paths.
- Update active root/app start scripts and runtime packaging hints.
- Strengthen residue guards.

## Acceptance

- `main_novaic.py` is the only active Agent Runtime process entrypoint.
- Task/saga/scheduler worker business classes do not accept unused gateway
  inputs.
- Active start scripts do not invoke unsupported `watchdog` mode or removed
  worker CLI flags.
- Tests fail if old launch helpers or retired entrypoints return.

## Closure Notes

- Deleted `novaic-agent-runtime/main_task.py`.
- Deleted `novaic-agent-runtime/main_saga.py`.
- Moved Saga worker registration and process-runner assembly into
  `main_novaic.py`.
- Removed module-local `start_worker` / `start_multiple_workers` helpers and
  direct `__main__` blocks from migrated worker modules.
- Updated `novaic-app/scripts/start-backends.sh` to launch task, saga,
  session-outbox, saga-outbox, health, and scheduler through `main_novaic.py`
  without removed worker flags.
- Updated `novaic-agent-runtime.spec` hidden imports away from retired sync
  module names.
- Expanded `tests/test_pr335_worker_residue_guards.py`.

## Verification

```bash
python -m compileall -q main_novaic.py task_queue/workers tests/test_pr335_worker_residue_guards.py
pytest -q tests/test_pr335_worker_residue_guards.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr328_health_generic_worker.py
pytest -q
bash -n scripts/start.sh
bash -n novaic-app/scripts/start-backends.sh
python scripts/ci/check_start_config_contract.py
pytest -q scripts/ci/test_no_legacy_file_hot_paths.py
```
