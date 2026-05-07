# C013: Worker Registry Residue Closure Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
rg -n "def _run_|_configure_|configure=|registry\\.run\\(|_run_session_outbox_worker|_run_saga_outbox_worker" task_queue/workers main_novaic.py tests -g '*.py'
pytest -q tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr330_task_worker_generic_source.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr337_worker_command_registry.py tests/test_pr335_worker_residue_guards.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr302_session_outbox_worker_production_wiring.py
```

## Result

- Static scan only matched guard strings inside tests.
- Expanded worker DSL/lifecycle suite passed: `36 passed`.
