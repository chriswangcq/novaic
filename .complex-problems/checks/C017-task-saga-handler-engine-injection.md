# C017: Task/Saga Handler Engine Injection Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
python -m compileall -q task_queue/workers tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py
rg -n "TaskQueueClient|BusinessClient|SagaClient|RetryPolicy|WorkerRuntimeDependencies|ServiceConfig|queue_service_url|business_url|saga_step_timeout|step_timeout|max_concurrent|def close\(" task_queue/workers/task_worker.py task_queue/workers/saga_worker.py tests/test_pr338_business_handlers_lifecycle_free.py -g '*.py'
pytest -q tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/test_pr338_business_handlers_lifecycle_free.py
pytest -q
```

## Result

- Static handler constructor/collaborator scan returned no matches.
- Targeted task/saga boundary suite: `24 passed`.
- Full runtime suite: `507 passed`.
