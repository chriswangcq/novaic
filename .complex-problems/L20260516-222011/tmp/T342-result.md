# Subagent finalize status payload identity result

## Summary

Implemented the wake-finalize terminal subagent status payload identity contract. Both `set_subagent_sleeping` and `set_subagent_completed` payload builders now emit current `scope_id` plus a strictly positive `session_generation`, using the shared session generation validator instead of defaulting missing generation to zero.

## Done

- Updated `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`.
- Added `_subagent_terminal_status_identity(ctx)` for terminal subagent status payloads.
- Changed `_session_generation(ctx)` to use `require_positive_session_generation(ctx, "wake_finalize")`.
- Preserved existing `agent_id/subagent_id` fields and `result: None` for completed payloads.
- Updated `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py` so PR-43 legacy tests now assert explicit identity and absence of `last_scope_id` residue.
- Added focused builder rejection coverage for missing and zero `session_generation`.

## Verification

- `python3 -m py_compile task_queue/sagas/wake_finalize.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py` passed: 18 tests.
- Source guard over `task_queue/sagas/wake_finalize.py` found no `last_scope_id`, `ctx.get("session_generation") or 0`, or `session_generation.*or 0` residue.

## Known Gaps

- Handler-side rejection before Business mutation is still owned by P358.
- DAG/session-ended gating before terminal subagent status mutation is still owned by P359.
- Aggregate residue verification is still owned by P360.

## Artifacts

- Code: `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
- Tests: `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py`
