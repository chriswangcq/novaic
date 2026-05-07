# C014: Worker Source Adapter Extraction Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
python -m compileall -q task_queue/workers
pytest -q tests/test_pr330_task_worker_generic_source.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/test_pr338_business_handlers_lifecycle_free.py
rg -n "class TaskQueueJobSource|class SagaClaimSource|TaskQueueJobSource|SagaClaimSource" task_queue/workers tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr330_task_worker_generic_source.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py -g '*.py'
```

## Result

- Targeted source/handler boundary suite: `15 passed`.
- Static scan shows source classes only in `task_sources.py` and
  `saga_sources.py`, with expected imports from assemblies/tests.
