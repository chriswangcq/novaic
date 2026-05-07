# P001: Declarative Worker Registry Perfect-Shape Cutover

Status: done
Parent: none
Ticket: T001

## Problem

Agent Runtime workers now share the generic worker substrate and a unified
`main_novaic.py` process entrypoint, but worker command assembly is still
scattered across individual `run_xxx_worker()` functions and `main()` has
explicit worker-mode branches. This is not the ideal shape: future worker
additions can bypass the substrate by adding bespoke entrypoint code.

## Success Criteria

- All Agent Runtime worker modes are declared in one `WorkerRegistry`.
- `main_novaic.py` delegates worker modes through the registry instead of
  having one branch and one run function per worker.
- Worker command parsing, `ServiceConfig` writes, process-runner assembly, and
  cleanup hooks are explicit registry definitions.
- Outbox workers use the same process runner as task/saga/health/scheduler.
- Static tests prove the registered worker modes and block reintroducing
  per-worker `main_novaic.py` branches.
- Runtime tests pass.

## Subproblems

- None initially; one focused cutover is possible with direct verification.

## Results

- All Agent Runtime worker modes are declared in
  `task_queue.workers.registry.WorkerRegistry`.
- `main_novaic.py` no longer contains one `run_xxx_worker()` function or one
  `elif mode == "<worker>"` branch per worker.
- Worker argparse setup, `ServiceConfig` mutation, process runner assembly,
  cleanup hooks, startup text, and worker construction are now registry-owned.
- Session and saga outbox workers now use `run_sync_worker_process`.
- PyInstaller hidden imports include `task_queue.workers.registry`.
- Static tests now guard the registry shape and reject reintroduced per-worker
  entrypoint functions/branches.

## Check

- `python -m compileall -q main_novaic.py task_queue/workers queue_service/worker tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr337_worker_command_registry.py`
- `pytest -q tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr334_worker_process_runner.py` -> 9 passed
- `pytest -q tests/test_pr323_generic_worker_contracts.py tests/test_pr324_generic_worker_loop.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py` -> 24 passed
- `pytest -q` in `novaic-agent-runtime` -> 491 passed
- worker help smoke for `task-worker`, `saga-worker`,
  `session-outbox-worker`, `saga-outbox-worker`, `health`, `scheduler`
- `bash -n scripts/start.sh`
- `bash -n novaic-app/scripts/start-backends.sh`
- `python scripts/ci/check_start_config_contract.py` -> OK
- `pytest -q scripts/ci/test_no_legacy_file_hot_paths.py` -> 1 passed
- `git diff --check` in root, `novaic-agent-runtime`, and `novaic-app`

## Follow-ups

- None for this problem. Remaining architectural work should start as a new
  problem only if the target shape changes beyond worker command registry.
