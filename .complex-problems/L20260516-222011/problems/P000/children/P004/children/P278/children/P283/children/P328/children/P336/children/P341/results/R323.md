# Wake-finalize payload positive generation result

## Summary

`wake_finalize` no longer emits `session.ended` payloads with implicit `generation=0`. It now requires `session_generation` to be present and positive before building the payload, with focused tests for missing and zero generation.

## Done

- Updated `novaic-agent-runtime/task_queue/sagas/wake_finalize.py::_session_generation(...)` to raise `ValueError` when `session_generation` is missing, `None`, or less than `1`.
- Kept `_build_session_ended_payload(...)` as the single payload-builder path while making its generation field fail closed through the strict extractor.
- Added `test_wake_finalize_payload_rejects_missing_or_zero_generation` in `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`.
- Preserved the existing valid positive-generation payload test.

## Verification

- Ran `python3 -m py_compile task_queue/sagas/wake_finalize.py`.
- Ran `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py`.
- Result: `7 passed in 0.12s`.
- Ran source guard against `session_generation") or 0` / `session_generation.*or 0` in `task_queue/sagas/wake_finalize.py`; no matches remain.

## Known Gaps

- `session.ended` handler and queue-service route still need earlier positive-generation validation; that is P342.
- Broader react-think/react-actions source contracts still default session generation to zero; that is outside this payload-builder child and remains delegated to P343/P337/P339.

## Artifacts

- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
