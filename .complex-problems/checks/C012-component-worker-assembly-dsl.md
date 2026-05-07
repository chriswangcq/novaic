# C012: Component Worker Assembly DSL Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
python -m compileall -q main_novaic.py task_queue/workers queue_service/session_outbox_worker.py queue_service/saga_outbox_worker.py
pytest -q tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr302_session_outbox_worker_production_wiring.py
pytest -q tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr330_task_worker_generic_source.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr302_session_outbox_worker_production_wiring.py
```

## Result

- Targeted registry/outbox suite: `19 passed`.
- Expanded worker DSL/lifecycle suite: `36 passed`.
- `registry.py` is now 117 lines, declares `WorkerSpec` data, and contains no `def _run_` or
  `def _configure_` paths.
