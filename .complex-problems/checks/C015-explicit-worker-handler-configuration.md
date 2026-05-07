# C015: Explicit Worker Handler Configuration Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
python -m compileall -q task_queue/workers
rg -n "ServiceConfig|task-worker-sync|saga-worker-sync|health-worker-sync|scheduler-sync|BusinessClient\(\s*ServiceConfig|or getattr\(ServiceConfig|or ServiceConfig" task_queue/workers tests/test_pr338_business_handlers_lifecycle_free.py tests/test_health_dispatch.py tests/test_scheduler_dispatch.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr331_task_worker_handler_cutover.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_high_concurrency_retry_replay.py -g '*.py'
pytest -q tests/test_pr331_task_worker_handler_cutover.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr328_health_generic_worker.py tests/test_health_dispatch.py tests/test_pr329_scheduler_generic_worker.py tests/test_scheduler_dispatch.py tests/test_pr338_business_handlers_lifecycle_free.py
pytest -q
```

## Result

- Static residue scan returned no matches.
- Targeted worker boundary suite: `40 passed`.
- Full runtime suite: `506 passed`.

## Stress Check

- Hidden configuration reads were not merely moved to another business module:
  `task_execution.py` and `wake/assembler_factory.py` are covered by the
  boundary guard in `test_pr338_business_handlers_lifecycle_free.py`.
- The only remaining `ServiceConfig` read for these workers is in
  `worker_assemblies.py`, the explicit process assembly boundary.
