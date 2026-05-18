# P358 success check

## Summary

Success. R335 solves the handler-validation problem: terminal subagent status handlers now require explicit finalize identity before Business mutation, tests cover the malformed inputs, and the Business update schema remains clean.

## Evidence

- `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py:62` defines `_require_terminal_finalize_identity()`.
- `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py:85` validates sleeping payload identity before `business_client` lookup and before `entity_update()`.
- `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py:130` validates completed payload identity before `business_client` lookup and before `entity_update()`.
- `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py:127` parameterizes both terminal handlers across missing scope, missing generation, zero generation, and malformed generation.
- `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py:162` asserts rejected payloads do not call `entity_update()`.
- `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py:98` and `:121` prove legacy last-scope fields are not written to Business; `:100` and `:123` also prove scope/generation are validation-only and not Business update fields.

## Criteria Map

- Inspect terminal status handlers: met by source evidence.
- Require `scope_id` and positive `session_generation` before `entity_update()`: met by `_require_terminal_finalize_identity()` calls before Business mutation.
- Keep Business update schema minimal: met by tests asserting no identity fields in update payloads.
- Add tests for missing scope, missing generation, zero generation, malformed generation before Business mutation: met by parameterized handler test.
- Keep non-finalize handlers unchanged unless direct dependency proven: met; `set_awake` was not modified.

## Execution Map

- Code changed: `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py`.
- Tests changed: `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py`.
- Commands run:
  - `python3 -m py_compile task_queue/handlers/subagent_handlers.py`
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py`
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py`

## Stress Test

- Plausible failure mode: a legacy `last_scope_id` payload without current wake identity flips Business status. The new parameterized tests cover missing `scope_id` and missing/invalid generation for both handlers and assert `entity_update()` is not called.

## Residual Risk

- A positive but stale generation still needs an upstream session-ended gate; that is explicitly owned by P359.
- Aggregate residue scanning is still owned by P360. These are non-blocking for local handler validation.

## Result IDs

- R335
