# C018: Health/Scheduler Action Engine Extraction Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
python -m compileall -q task_queue/workers tests/test_health_dispatch.py tests/test_pr328_health_generic_worker.py tests/test_scheduler_dispatch.py tests/test_pr329_scheduler_generic_worker.py
rg -n "BusinessClient|internal_sync_client|get_assembler|DispatchAssembler|httpx|queue_service_url|business_url|task_timeout|saga_timeout|queue_internal_key|WorkerRuntimeDependencies|def close\(|_get_client|_perform_check|_check_and_wake|_recover_queue" task_queue/workers/health_worker.py task_queue/workers/scheduler_worker.py -g '*.py'
pytest -q tests/test_pr43_previous_scope_transport.py tests/test_health_dispatch.py tests/test_scheduler_dispatch.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr338_business_handlers_lifecycle_free.py
pytest -q
```

## Result

- Static health/scheduler handler residue scan returned no matches.
- Targeted health/scheduler boundary suite: `28 passed`.
- Full runtime suite: `508 passed`.
