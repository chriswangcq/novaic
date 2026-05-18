# Direct session-ended delivery residue guard result

## Summary

Direct session-ended delivery residue guards are clean. The checked files no longer contain the zero-generation wake-finalize fallback, handler presence-only generation validation, or plain route `generation: int`; the SagaClient path validates generation before the `/api/queue/session-ended` request.

## Done

- Ran source guards over direct delivery files:
  - `task_queue/sagas/wake_finalize.py`
  - `task_queue/handlers/session_handlers.py`
  - `task_queue/client.py`
  - `queue_service/routes.py`
- Confirmed `SagaClient.session_ended(...)` calls `_require_positive_generation(generation)` before `_request("POST", "/api/queue/session-ended", ...)`.
- Ran focused finalize and legacy boundary tests.

## Verification

- `! rg -n 'session_generation"\\) or 0|session_generation.*or 0' task_queue/sagas/wake_finalize.py`
- `! rg -n 'if generation is None' task_queue/handlers/session_handlers.py`
- `! rg -n 'generation:\\s*int\\s*$' queue_service/routes.py`
- `rg -n '_require_positive_generation\\(generation\\)|"/api/queue/session-ended"' task_queue/client.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr255_legacy_compat_cleanup.py`
- Result: `14 passed in 0.28s`.

## Known Gaps

- Test-level and upstream react contract residue are handled by sibling P346/P347.

## Artifacts

- Guard output: `task_queue/client.py` has `_require_positive_generation(generation)` immediately before `_request("POST", "/api/queue/session-ended", ...)`.
