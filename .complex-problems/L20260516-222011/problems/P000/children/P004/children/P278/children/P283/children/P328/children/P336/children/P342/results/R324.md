# Session-ended handler client route contract result

## Summary

The session-ended delivery boundary now rejects non-positive generation at the handler, Saga client, and route schema before repository mutation. During testing, I found the method lives on `SagaClient`, not `TaskQueueClient`; the implementation and tests were corrected to match the actual live client boundary.

## Done

- Added `_positive_generation(...)` in `novaic-agent-runtime/task_queue/handlers/session_handlers.py` and made `handle_session_ended(...)` reject missing, bool, non-castable, zero, or negative generation before calling the client.
- Added `_require_positive_generation(...)` in `novaic-agent-runtime/task_queue/client.py` and made `SagaClient.session_ended(...)` reject non-positive generation before HTTP request.
- Updated `novaic-agent-runtime/queue_service/routes.py::SessionEndedRequest` to declare `generation: int = Field(gt=0)`.
- Extended `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py` with:
  - handler zero-generation rejection and no extra client call.
  - SagaClient zero-generation rejection before `_request`.
  - route model non-positive generation rejection.
  - valid SagaClient and route preservation checks.

## Verification

- Ran `python3 -m py_compile task_queue/handlers/session_handlers.py task_queue/client.py queue_service/routes.py`.
- Ran `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py`.
- Result: `9 passed in 0.21s`.
- Ran focused broader suite: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr255_legacy_compat_cleanup.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr241_pending_inbox_projection.py tests/test_pr251_wake_creation_outbox_cutover.py`.
- Result: `25 passed in 0.32s`.
- Source guard for `if generation is None` in `task_queue/handlers/session_handlers.py` is clean.

## Known Gaps

- The broader upstream react contracts still default session generation to zero; that remains outside P342 and is assigned to P343/P337/P339.
- `wake_finalize` was already hardened in P341; aggregate verification remains P344.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/session_handlers.py`
- `novaic-agent-runtime/task_queue/client.py`
- `novaic-agent-runtime/queue_service/routes.py`
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
