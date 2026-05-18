# Round and stack-depth default classification result

## Summary

Patched wake-finalize and recovery metadata parsing so `round_num` and `stack_depth_at_finalize` use explicit non-negative integer parsing instead of raw `int(... or 0)` defaults.

## Done

- Added `_non_negative_int` to `task_queue/sagas/wake_finalize.py`.
- Added `_non_negative_int` to `queue_service/session_recovery.py`.
- Updated wake finalize cortex/session-ended payload builders to parse `round_num` explicitly.
- Updated wake finalize remaining-stack fallback and recovery archive fallback to parse `stack_depth_at_finalize` explicitly.
- Added focused tests rejecting bool `round_num` and bool `stack_depth_at_finalize` in wake finalize and recovery archive paths.

## Verification

- `python3 -m py_compile task_queue/sagas/wake_finalize.py queue_service/session_recovery.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr266_session_recovery_boundary.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py` passed: 30 tests.
- Targeted guard for raw stack-depth/round parsing now shows only explicit helper calls in wake finalize; recovery raw defaults are removed.

## Known Gaps

- Remaining guard hits are helper usages, not raw defaults.

## Artifacts

- Patched files: `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`, `novaic-agent-runtime/queue_service/session_recovery.py`, `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`, `novaic-agent-runtime/tests/test_pr266_session_recovery_boundary.py`.
