# Runtime attach active generation validation result

## Summary

Patched the runtime session attach path so active session generation is validated explicitly instead of silently coerced with `int(... or 0)`.

## Done

- Updated `novaic-agent-runtime/queue_service/session_repo.py` to call `_require_positive_generation(current_active.get("generation"), "active session attach")`.
- Removed the local follow-up `if session_generation < 1` branch because the shared helper now owns that validation and rejects bool, missing, non-integer, and non-positive values.

## Verification

- `python3 -m py_compile queue_service/session_repo.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr238_generation_checked_attach.py tests/test_pr254_finalize_ownership.py tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr259_generic_fsm_store_outbox.py` passed: 26 tests.
- Focused source check no longer shows `session_generation = int(current_active...)`; it shows the attach path using `_require_positive_generation`.

## Known Gaps

- Other session repo generation adapters still contain raw `int((active_session or {}).get("generation") or 0)` and `int(state.get("generation") or 0)` in reconstruction/adapter code. They are outside the active attach-path target and should be classified in the cross-repo guard matrix.

## Artifacts

- Patched file: `novaic-agent-runtime/queue_service/session_repo.py`.
