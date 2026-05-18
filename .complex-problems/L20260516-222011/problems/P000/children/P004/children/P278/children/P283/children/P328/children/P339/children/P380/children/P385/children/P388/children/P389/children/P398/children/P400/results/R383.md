# Subagent wake session generation boundary result

## Summary

The subagent wake session-init payload builder now treats `session_generation` as a required live session boundary. It reuses the shared positive session generation contract instead of inline `int(...)` coercion.

## Done

- Updated `novaic-agent-runtime/task_queue/sagas/subagent_wake.py` to call `require_positive_session_generation(ctx, "subagent_wake")`.
- Removed the optional `ctx.get("session_generation") is not None` branch and the raw `int(ctx["session_generation"])` conversion.
- Updated direct builder tests and session-init fixtures to pass explicit session generation.
- Added `test_saga_payload_requires_positive_session_generation` to cover missing, zero, bool, and malformed values.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_session_init_message_ids.py tests/test_pr43_previous_scope_transport.py` -> `13 passed in 0.07s`.
- Broader related suite passed: `PYTHONPATH=.:../novaic-common pytest -q tests/test_session_init_message_ids.py tests/test_pr43_previous_scope_transport.py tests/test_pr65_agent_root_scope.py tests/test_pr67_wake_child_scope.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_saga_creation_policy_boundary.py` -> `41 passed in 0.34s`.
- `rg -n "int\\(ctx\\[\\\"session_generation\\\"\\]\\)|ctx\\.get\\(\\\"session_generation\\\"\\) is not None|payload\\[\\\"session_generation\\\"\\] = int" novaic-agent-runtime/task_queue/sagas/subagent_wake.py novaic-agent-runtime/tests/test_session_init_message_ids.py` returned no matches.

## Known Gaps

- This closes the subagent wake `session_generation` boundary only. The final widened residue matrix is still open under P401.

## Artifacts

- `novaic-agent-runtime/task_queue/sagas/subagent_wake.py`
- `novaic-agent-runtime/tests/test_session_init_message_ids.py`
- `novaic-agent-runtime/tests/test_pr43_previous_scope_transport.py`
- `novaic-agent-runtime/tests/test_pr65_agent_root_scope.py`
- `novaic-agent-runtime/tests/test_pr67_wake_child_scope.py`
