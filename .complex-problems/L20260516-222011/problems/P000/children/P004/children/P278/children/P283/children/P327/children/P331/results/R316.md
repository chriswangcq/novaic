# Attach session outbox delivery audit result

## Summary

Completed the attach outbox delivery audit and strengthened coverage. `SessionOutboxDispatcher._publish_attach_input(...)` already fails closed on missing `expected_session_generation` before publishing the task, and preserves expected generation/scope in `session.attach_input` payload. Added a direct behavior test so this contract is not only source-guarded.

## Done

- Mapped `session_effects.py::build_attach_input_effect(...)` payload shape: includes `expected_wake_scope_id` and `expected_session_generation`.
- Mapped `session_outbox.py::_publish_attach_input(...)`: validates message ids, scope id, expected generation, agent/subagent, then publishes `TaskTopics.SESSION_ATTACH_INPUT` with `expected_wake_scope_id` and integer `expected_session_generation`.
- Added `test_attach_outbox_delivery_requires_expected_generation` to verify missing expected generation raises before publish.
- Verified existing attach outbox cutover tests assert generated outbox/task payload generation.

## Verification

- `python3 -m py_compile queue_service/session_outbox.py queue_service/session_effects.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr255_legacy_compat_cleanup.py`
  - Result: `15 passed in 0.11s`.
- Broader attach boundary run:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr248_attach_outbox_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr255_legacy_compat_cleanup.py`
  - Result: `26 passed in 0.21s`.

## Known Gaps

- P332 still needs runtime handler enforcement audit.
- P333 still needs aggregate stale/missing attach regression audit.

## Artifacts

- `novaic-agent-runtime/queue_service/session_outbox.py`
- `novaic-agent-runtime/queue_service/session_effects.py`
- `novaic-agent-runtime/tests/test_pr267_session_outbox_effect_boundary.py`
- `novaic-agent-runtime/tests/test_pr248_attach_outbox_cutover.py`
