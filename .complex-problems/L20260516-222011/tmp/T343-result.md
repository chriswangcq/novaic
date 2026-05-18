# Subagent finalize status handler validation result

## Summary

Implemented terminal subagent status handler identity validation. `set_sleeping` and `set_completed` now require `scope_id` and positive `session_generation` before Business status mutation, while `set_awake` remains unchanged.

## Done

- Updated `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py`.
- Added `_require_terminal_finalize_identity(payload, owner)`.
- Reused the shared session generation validator and converted invalid identity into `ValidationError`.
- Called the validator before `business_client` lookup, update construction, and `entity_update()` in terminal handlers.
- Kept Business update payloads minimal: no `scope_id`, `session_generation`, `last_scope_id`, or `last_scope_archived_at` is written to Business.
- Updated `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py`.
- Added rejection coverage for both terminal handlers across missing `scope_id`, missing generation, zero generation, and malformed generation.

## Verification

- `python3 -m py_compile task_queue/handlers/subagent_handlers.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py` passed: 13 tests.
- Broader focused suite passed: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py` -> 39 tests.
- Source review confirmed `task_queue/handlers/subagent_handlers.py` has no generation defaulting and no `last_scope_id` residue.

## Known Gaps

- Stale generation comparison still depends on the session-ended gate owned by P359.
- Aggregate residue verification remains P360.

## Artifacts

- Code: `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py`
- Tests: `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py`
