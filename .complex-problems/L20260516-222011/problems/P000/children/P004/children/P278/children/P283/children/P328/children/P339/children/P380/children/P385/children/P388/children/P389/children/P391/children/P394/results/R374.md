# Session repo state reconstruction validation result

## Summary

Patched session repo runtime-state reconstruction so generation validation is explicit by lifecycle status instead of raw `int(... or 0)` defaults.

## Done

- Added `_require_non_negative_generation` and `_runtime_generation_for_status` to `queue_service/session_repo.py`.
- Updated `_decide_live_dispatch` and `_runtime_state_from_session_state`:
  - `NO_ACTIVE` can use generation `0`.
  - Active-like states require positive generation.
  - Bool/malformed values fail loudly.
- Added focused session state taxonomy tests for active bool/zero rejection and no-active bool rejection.

## Verification

- `python3 -m py_compile queue_service/session_repo.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr283_session_state_taxonomy.py tests/test_pr253_dispatch_pure_fsm_cutover.py tests/test_pr238_generation_checked_attach.py tests/test_pr254_finalize_ownership.py tests/test_pr264_session_finalize_fsm_boundary.py` passed: 32 tests.
- Targeted source guard for the old session repo reconstruction raw defaults returned no matches.

## Known Gaps

- Session ledger active generation helper defaults are left for sibling P395.

## Artifacts

- Patched files: `novaic-agent-runtime/queue_service/session_repo.py`, `novaic-agent-runtime/tests/test_pr283_session_state_taxonomy.py`.
