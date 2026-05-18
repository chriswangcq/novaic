# Session FSM finalize generation validation result

## Summary

Patched the pure session FSM finalize reducer so it no longer silently coerces finalize/current generation with raw `int(... or 0)`.

## Done

- Added explicit local generation helpers in `queue_service/session_fsm.py`:
  - `_positive_generation_or_none` for finalize event generation.
  - `_require_non_negative_generation` for current FSM state generation.
- Updated `_reduce_session_finalize` to reject malformed finalize generation as `missing_generation` and to reject malformed state generation with a clear `ValueError`.
- Added focused tests for bool finalize generation and bool state generation.

## Verification

- `python3 -m py_compile queue_service/session_fsm.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr254_finalize_ownership.py tests/test_pr258_generic_fsm_substrate.py tests/test_pr285_session_fsm_decision_contract.py` passed: 21 tests.
- Focused guard `rg -n "finalize_generation\\s*=\\s*int|current_generation\\s*=\\s*int|int\\([^\\n]*(finalize_generation|state\\.generation)" queue_service/session_fsm.py` returned no matches.

## Known Gaps

- Session repo/ledger adapters and audit/generic FSM hits are intentionally left for sibling P391/P392/P393 problems.

## Artifacts

- Patched files: `novaic-agent-runtime/queue_service/session_fsm.py`, `novaic-agent-runtime/tests/test_pr264_session_finalize_fsm_boundary.py`.
