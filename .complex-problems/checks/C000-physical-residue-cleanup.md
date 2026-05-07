# C000: Physical Residue Cleanup Check

Problem: P000
Ticket: T000
Status: passed

## Commands

```bash
cd novaic-agent-runtime
python -m compileall -q main_novaic.py task_queue/workers tests/test_pr335_worker_residue_guards.py
pytest -q tests/test_pr335_worker_residue_guards.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr328_health_generic_worker.py
pytest -q

cd ..
bash -n scripts/start.sh
bash -n novaic-app/scripts/start-backends.sh
python scripts/ci/check_start_config_contract.py
pytest -q scripts/ci/test_no_legacy_file_hot_paths.py
```

## Results

- Compileall: passed.
- Targeted worker tests: 23 passed.
- Runtime full suite: 487 passed.
- Root/app startup script syntax: passed.
- Start config contract: passed.
- Legacy file hot-path guard: 1 passed.
