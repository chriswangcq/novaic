# Result: P432 / T420 direct scope-end contract cleanup

## Summary

Audited and verified the direct `/v1/scope/end` contract. The current implementation already enforces structured archive diagnostics when diagnostics are supplied, rejects structural `report`, appends wake archive events, and finalizes active stack projection through explicit helpers.

## Verification

- Focused test command:
  - `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_read_source_guards.py tests/test_active_stack_projection.py tests/test_scope_state.py`
- Result: `63 passed in 0.56s`

## Contract Evidence

- `ScopeEndRequest` validates:
  - bool `session_generation` rejected
  - positive `session_generation` required when diagnostics are supplied
  - non-empty `finalize_reason` required when diagnostics are supplied
  - `remaining_stack` required when diagnostics are supplied
- `scope_end` rejects non-empty structural reports.
- `scope_end` calls `_append_wake_archived_event` before archive projection.
- `scope_end` calls `_finalize_active_stack_for_archive` for root and wake child finalization.
- Retry/idempotent behavior is covered by focused tests.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p432/focused-pytest.with-status.txt`
- `.complex-problems/L20260516-222011/tmp/p432/scope-end-contract-guard.txt`

## Conclusion

No direct scope-end contract patch was required. No live P432 gap remains.
