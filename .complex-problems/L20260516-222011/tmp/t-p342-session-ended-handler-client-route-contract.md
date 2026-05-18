# Session-ended handler client route contract

## Problem Definition

The `session.ended` delivery boundary still validates generation too late or too weakly. `handle_session_ended(...)` rejects only missing generation, then casts with `int(...)`; `SessionEndedRequest` accepts plain `int`; `TaskQueueClient.session_ended(...)` forwards without an explicit local guard. This permits zero or negative generation to pass across the delivery boundary until repository validation catches it.

## Proposed Solution

1. Add a small shared positive-generation validation shape at the delivery boundary without creating a broad new abstraction.
2. Update `task_queue/handlers/session_handlers.py` so `generation` must be present and `>= 1` before calling the client.
3. Update `task_queue/client.py::TaskQueueClient.session_ended(...)` to fail fast for non-positive generation before making the HTTP request.
4. Update `queue_service/routes.py::SessionEndedRequest` to use a positive integer constraint for `generation`.
5. Extend tests to prove:
   - handler rejects zero generation before client call.
   - client rejects zero generation before request.
   - route schema rejects zero/non-positive generation.
   - valid payload still forwards all contract fields unchanged.

## Acceptance Criteria

- `session.ended` handler rejects missing, zero, negative, or non-castable generation before client delivery.
- Client rejects non-positive generation before HTTP request.
- Queue-service route schema rejects non-positive generation.
- Existing valid finalize delivery tests still pass.
- Focused tests cover handler, client, and route validation.

## Verification Plan

- `python3 -m py_compile task_queue/handlers/session_handlers.py task_queue/client.py queue_service/routes.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py`
- Add/run focused route/client tests if no existing file is appropriate.
- Source guard for `if generation is None`-only validation in `session_handlers.py` after the patch.

## Risks

- Pydantic version differences may affect positive integer syntax; choose the style already compatible with the repository dependencies.
- Some tests may instantiate route request models directly with zero generation; rewrite them instead of preserving compatibility.

## Assumptions

- No backward compatibility is required for zero or negative session-ended generation.
