# P002 Result - Worker DSL 与 roster SSOT 收口

## Done
- Added canonical runtime roster module `task_queue.workers.runtime_roster`.
- Added shell-facing CLI `novaic-agent-runtime/scripts/runtime_worker_roster.py`.
- `WorkerRegistry` now preserves canonical worker mode order from `RUNTIME_WORKER_MODES`.
- `scripts/start.sh` verifies required runtime subprocesses by consuming `runtime_worker_roster.py process-checks`.
- `deploy status` consumes the same process roster instead of hard-coded `check_role` calls.
- Deploy fresh-smoke consumes `runtime_worker_roster.py log-files` for runtime/subscriber logs.
- Updated CI guards to verify roster consumption and reject duplicated hard-coded role checks.
- Updated deploy runbook to point to the runtime roster SSOT.
- Added `tests/test_pr343_runtime_worker_roster_ssot.py`.

## Verification
- `python3 scripts/ci/lint_runtime_worker_supervision.py`
- `python3 scripts/ci/lint_deploy_fresh_smoke.py`
- `bash -n scripts/start.sh`
- `bash -n deploy`
- `python3 -m py_compile novaic-agent-runtime/task_queue/workers/command_specs.py novaic-agent-runtime/task_queue/workers/runtime_roster.py novaic-agent-runtime/task_queue/workers/registry.py novaic-agent-runtime/scripts/runtime_worker_roster.py scripts/ci/lint_runtime_worker_supervision.py scripts/ci/lint_deploy_fresh_smoke.py`
- `pytest -q tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr343_runtime_worker_roster_ssot.py`
- `pytest -q tests/test_pr323_generic_worker_contracts.py tests/test_pr324_generic_worker_loop.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/test_pr334_worker_process_runner.py tests/test_pr335_worker_residue_guards.py tests/test_pr337_worker_command_registry.py tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr343_runtime_worker_roster_ssot.py`

All targeted checks passed: 54 tests in the worker regression group.

## Artifacts
- `novaic-agent-runtime/task_queue/workers/runtime_roster.py`
- `novaic-agent-runtime/scripts/runtime_worker_roster.py`
- `novaic-agent-runtime/task_queue/workers/registry.py`
- `novaic-agent-runtime/task_queue/workers/command_specs.py`
- `scripts/start.sh`
- `deploy`
- `scripts/ci/lint_runtime_worker_supervision.py`
- `scripts/ci/lint_deploy_fresh_smoke.py`
- `docs/runbooks/deploy.md`
- `novaic-agent-runtime/tests/test_pr343_runtime_worker_roster_ssot.py`
- `novaic-agent-runtime/tests/test_pr337_worker_command_registry.py`

## Remaining Gaps
- Start logic still has explicit launch loops for task/saga/outbox/health/scheduler processes. This ticket makes the roster SSOT; a later ticket can make launch command generation itself fully roster-driven if desired.
