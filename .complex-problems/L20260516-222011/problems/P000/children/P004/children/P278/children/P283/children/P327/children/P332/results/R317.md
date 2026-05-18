# Runtime attach handler generation enforcement audit result

## Summary

Completed runtime attach handler enforcement audit and strengthened coverage. `handle_session_attach_input(...)` validates required expected wake scope and expected generation before reading current root meta, then rejects stale wake scope or stale generation before appending input or claiming notifications.

## Done

- Mapped runtime handler source: `task_queue/handlers/runtime_handlers.py::handle_session_attach_input`.
- Verified required fields:
  - `expected_wake_scope_id` is required.
  - `expected_session_generation` is required.
- Verified stale checks:
  - Current root meta `current_wake_scope_id` must match `expected_wake_scope_id`.
  - Current root meta `current_session_generation` must match `expected_session_generation`.
- Added direct missing `expected_wake_scope_id` regression coverage.
- Existing tests already verify missing generation, stale wake scope, stale generation, and happy-path append/claim.

## Verification

- `python3 -m py_compile task_queue/handlers/runtime_handlers.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr238_generation_checked_attach.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr255_legacy_compat_cleanup.py`
- Result: `18 passed in 0.17s`.

## Known Gaps

- P333 still needs aggregate stale/missing attach regression coverage across repository, outbox, and runtime after these fixes.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
- `novaic-agent-runtime/tests/test_pr238_generation_checked_attach.py`
- `novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py`
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
