# R013: Worker Registry Residue Closure Result

## Outcome

Updated stale tests that still expected bespoke registry run/configure sections.
Tests now assert the new shape:

- registry has no `_configure_*` or `_run_*` functions
- registry points at `assemble_*_worker` build-process factories
- component assembly contains concrete `GenericWorker`/handler construction
- business handler modules remain lifecycle-free

## Files Changed

- `novaic-agent-runtime/tests/test_pr337_worker_command_registry.py`
- `novaic-agent-runtime/tests/test_pr326_session_outbox_generic_worker.py`
- `novaic-agent-runtime/tests/test_pr327_saga_outbox_generic_worker.py`
- `novaic-agent-runtime/tests/test_pr302_session_outbox_worker_production_wiring.py`
- `novaic-agent-runtime/tests/test_pr338_business_handlers_lifecycle_free.py`
- `novaic-agent-runtime/tests/test_pr331_task_worker_handler_cutover.py`
- `novaic-agent-runtime/tests/test_pr333_saga_worker_handler_cutover.py`

## Notes

This closes the old-test residue where tests preserved the pre-DSL registry
shape by looking for `_run_session_outbox_worker` and `_run_saga_outbox_worker`.
