# C001: Worker Registry Perfect-Shape Check

Problem: P001
Ticket: T001
Status: passed
Date: 2026-05-07

## Verification Commands

```bash
cd /Users/wangchaoqun/new-build-novaic/novaic-agent-runtime
python -m compileall -q main_novaic.py task_queue/workers queue_service/worker tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr337_worker_command_registry.py
pytest -q tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr334_worker_process_runner.py
pytest -q tests/test_pr323_generic_worker_contracts.py tests/test_pr324_generic_worker_loop.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py
pytest -q
for mode in task-worker saga-worker session-outbox-worker saga-outbox-worker health scheduler; do python main_novaic.py "$mode" --help >/dev/null || exit 1; done
```

```bash
cd /Users/wangchaoqun/new-build-novaic
bash -n scripts/start.sh
bash -n novaic-app/scripts/start-backends.sh
python scripts/ci/check_start_config_contract.py
pytest -q scripts/ci/test_no_legacy_file_hot_paths.py
git diff --check
```

```bash
cd /Users/wangchaoqun/new-build-novaic/novaic-agent-runtime
git diff --check
```

```bash
cd /Users/wangchaoqun/new-build-novaic/novaic-app
git diff --check
```

## Observed Output

- Registry/residue/process-runner tests: `9 passed`
- Worker migration tests: `24 passed`
- Runtime full suite: `491 passed`
- Root start/config checks:
  - `start_config_contract OK`
  - legacy hot-path test: `1 passed`
- All compile and diff-check commands passed.

## Residue Audit

Static search found no per-worker `main_novaic.py` run functions or worker mode
branches for:

- `task-worker`
- `saga-worker`
- `session-outbox-worker`
- `saga-outbox-worker`
- `health`
- `scheduler`

The only remaining `--gateway-url` matches are Business and Device service
startup parameters in `scripts/start.sh`; they are not worker compatibility
branches.
