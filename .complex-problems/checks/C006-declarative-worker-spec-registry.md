# C006: Declarative WorkerSpec Registry Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
python -m compileall -q task_queue/workers main_novaic.py queue_service/worker queue_service/session_outbox_worker.py queue_service/saga_outbox_worker.py
pytest -q tests/test_pr337_worker_command_registry.py tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py
pytest -q
```

Ran from repo root:

```bash
rg -n "WorkerSync|TaskWorkerSync|SagaWorkerSync|HealthWorkerSync|SchedulerWorkerSync|registry owns GenericWorker|Parser setup and process assembly|491 passed|P004 todo|P006 todo|Pending P003" docs/architecture/generic-worker-substrate-plan.md docs/roadmap/tickets/PR-328-health-generic-worker.md docs/roadmap/tickets/PR-329-scheduler-generic-worker.md docs/roadmap/tickets/PR-331-task-worker-handler-cutover.md docs/roadmap/tickets/PR-333-saga-worker-handler-cutover.md docs/roadmap/tickets/PR-337-worker-command-registry.md docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md
```

## Result

- Compile passed.
- Targeted WorkerSpec/lifecycle suite: `23 passed`.
- Full `novaic-agent-runtime` suite: `504 passed`.
- Current architecture/ticket docs no longer contain the checked stale
  WorkerSync/current-shape phrases.
