# Wake finalize stack strictness result

## Summary

Implemented strict wake finalize `remaining_stack` handling. `wake_finalize.py` now rejects missing/non-dict `remaining_stack`, React finalize producers no longer emit legacy `stack_*_at_finalize` fields, and saga compensation now provides an explicit unknown-stack snapshot when the failed saga context has no stack.

## Done

- Updated `task_queue/sagas/wake_finalize.py` to require `remaining_stack` instead of synthesizing it from fallback fields.
- Updated `queue_service/saga_repo.py` compensation producer to add explicit `{"known": false, "depth": 0, "frames": []}` when no stack is available.
- Removed `stack_depth_at_finalize` / `stack_known_at_finalize` from React finalize context producers.
- Updated focused tests and added compensation coverage for missing stack.

## Verification

- Focused tests passed from `novaic-agent-runtime`:
  - `tests/test_finalize_summary_boundary.py`
  - `tests/test_pr234_repeated_scope_mismatch.py`
  - `tests/test_pr254_finalize_ownership.py`
  - `tests/test_pr255_legacy_compat_cleanup.py`
  - `tests/test_pr311_saga_compensation_outbox_cutover.py`
  - `tests/test_pr48_turn_finalizer.py`
- Test artifact: `.complex-problems/L20260516-222011/tmp/p494/wake-finalize-strictness-tests.log` (`53 passed in 0.37s`).
- Guard artifact: `.complex-problems/L20260516-222011/tmp/p494/wake-finalize-strictness-guards.txt`, showing no remaining `stack_depth_at_finalize` / `stack_known_at_finalize` hits in finalizer/producers/tests covered by P494.

## Known Gaps

- Recovery archive fallback in `session_recovery.py` is still intentionally left for P491.

## Artifacts

- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/task_queue/contracts/react_actions.py`
- `novaic-agent-runtime/task_queue/contracts/react_think.py`
- `novaic-agent-runtime/tests/test_finalize_summary_boundary.py`
- `novaic-agent-runtime/tests/test_pr234_repeated_scope_mismatch.py`
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- `novaic-agent-runtime/tests/test_pr311_saga_compensation_outbox_cutover.py`
- `novaic-agent-runtime/tests/test_pr48_turn_finalizer.py`
- `.complex-problems/L20260516-222011/tmp/p494/wake-finalize-strictness-tests.log`
- `.complex-problems/L20260516-222011/tmp/p494/wake-finalize-strictness-guards.txt`
