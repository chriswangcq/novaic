# P007 Result - Roster-driven runtime launch generation

## Done
- Extended `RuntimeProcessRole` with canonical `launch_commands`.
- Added `runtime_launch_commands()` and CLI command `runtime_worker_roster.py launch-commands`.
- Replaced manual worker launch loops/blocks in `scripts/start.sh` with `runtime_roster launch-commands`.
- Added tests that CLI launch output matches canonical roster.
- Added lint checks that reject reintroduced manual launch loops in `scripts/start.sh`.

## Verification
- `python3 scripts/ci/lint_runtime_worker_supervision.py`
- `python3 scripts/ci/lint_deploy_fresh_smoke.py`
- `bash -n scripts/start.sh`
- `bash -n deploy`
- `pytest -q tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr343_runtime_worker_roster_ssot.py`
- `pytest -q tests/test_pr323_generic_worker_contracts.py tests/test_pr324_generic_worker_loop.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/test_pr334_worker_process_runner.py tests/test_pr335_worker_residue_guards.py tests/test_pr337_worker_command_registry.py tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr343_runtime_worker_roster_ssot.py`

All targeted checks passed: 54 tests in the worker regression group.

## Artifacts
- `novaic-agent-runtime/task_queue/workers/runtime_roster.py`
- `novaic-agent-runtime/scripts/runtime_worker_roster.py`
- `scripts/start.sh`
- `scripts/ci/lint_runtime_worker_supervision.py`
- `novaic-agent-runtime/tests/test_pr343_runtime_worker_roster_ssot.py`

## Remaining Gaps
- None for this follow-up ticket.
