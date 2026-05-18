# PR-337: Declarative Worker Command Registry

Status: Closed
Owner: Codex
Problem: P001
Phase: 8

## Context

PR-336 physically removed retired standalone worker entrypoints and made
`main_novaic.py` the single Agent Runtime executable for task, saga, health,
scheduler, and durable outbox workers. That removed old files, but command
assembly was still scattered through one `run_xxx_worker()` function per worker
mode.

AI-era cleanup requires the remaining business entry wiring to be mechanically
hard to bypass: a future worker should be added as a registry entry, not as a
fresh imperative branch.

## Goal

Move all Agent Runtime worker command assembly into
`task_queue.workers.registry.WorkerRegistry`.

## Scope

- `novaic-agent-runtime/main_novaic.py`
- `novaic-agent-runtime/task_queue/workers/registry.py`
- `novaic-agent-runtime/novaic-agent-runtime.spec`
- worker residue and registry tests

## Non-Goals

- No task/saga/session FSM behavior changes.
- No Queue Service schema changes.
- No new worker modes.

## Acceptance

- Registry declares exactly:
  - `task-worker`
  - `saga-worker`
  - `session-outbox-worker`
  - `saga-outbox-worker`
  - `health`
  - `scheduler`
- `main_novaic.py` has no per-worker `run_xxx_worker()` functions.
- `main_novaic.py` has no per-worker `elif mode == "<worker>"` branches.
- Parser setup lives in declarative `WorkerSpec` data in the registry.
- Concrete process assembly lives in component-level `worker_assemblies.py`
  factories.
- Outbox workers use `run_sync_worker_process`.
- PyInstaller hidden imports include the registry module.
- Static tests guard the new shape.

## Verification

```bash
cd novaic-agent-runtime
python -m compileall -q main_novaic.py task_queue/workers queue_service/worker tests/test_pr337_worker_command_registry.py
pytest -q tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr334_worker_process_runner.py tests/test_pr323_generic_worker_contracts.py tests/test_pr324_generic_worker_loop.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py
pytest -q
```

Root checks:

```bash
bash -n scripts/start.sh
bash -n novaic-app/scripts/start-backends.sh
python scripts/ci/check_start_config_contract.py
pytest -q scripts/ci/test_no_legacy_file_hot_paths.py
```

## Deletion Criteria

- Delete the remaining per-worker run functions from `main_novaic.py`.
- Delete the remaining per-worker worker-mode branches from `main_novaic.py`.
- Do not leave compatibility wrappers for old branch names.

## Closure

- `task_queue.workers.registry` owns all worker command specs.
- `task_queue.workers.worker_assemblies` owns concrete worker process
  assembly.
- `main_novaic.py` delegates all worker modes through
  `run_worker_mode_if_registered`.
- Static tests reject the deleted per-worker function/branch shape.
- Verification completed:
  - `pytest -q` in `novaic-agent-runtime` -> 504 passed after PR-338/P006
    WorkerSpec tightening
  - worker help smoke for all six worker modes
  - root start/config checks
  - `git diff --check`
