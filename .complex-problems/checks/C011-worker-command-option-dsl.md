# C011: Worker Command Option DSL Check

## Verification

Ran from `novaic-agent-runtime`:

```bash
python -m compileall -q task_queue/workers/registry.py
pytest -q tests/test_pr337_worker_command_registry.py
rg -n "_configure_|configure=|class WorkerCommand|WorkerOption|def _run_.*worker" task_queue/workers/registry.py
```

## Result

- Registry compiles.
- `tests/test_pr337_worker_command_registry.py` passed after adding the static
  guard: `5 passed`.
- Static scan found `WorkerOption` data and remaining `_run_*` assembly
  functions, but no `_configure_*` or `configure=` residue. Remaining assembly
  functions are the explicit scope of P012/P013.
