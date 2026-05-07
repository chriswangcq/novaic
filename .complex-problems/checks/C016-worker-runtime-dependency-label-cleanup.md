# C016: Worker Runtime Dependency Label Cleanup Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
rg -n "TaskWorkerSync|SagaWorkerSync|HealthWorkerSync|SchedulerWorkerSync|task-worker-sync|saga-worker-sync|health-worker-sync|scheduler-sync|task-sync|saga-sync" task_queue/workers tests/test_pr338_business_handlers_lifecycle_free.py -g '*.py'
rg -n "ServiceConfig" task_queue/workers tests/test_pr338_business_handlers_lifecycle_free.py -g '*.py'
pytest -q tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py
```

## Result

- Retired sync label scan returned no matches.
- `ServiceConfig` scan returned no matches in worker modules.
- Targeted worker boundary suite: `14 passed`.
