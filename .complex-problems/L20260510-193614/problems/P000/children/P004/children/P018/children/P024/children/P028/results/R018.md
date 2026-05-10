# Phase 3B3B Scope Archive Finalize Wiring Result

## Summary

Wired live `scope_end` archive paths through the active-stack finalize helper. Archive now snapshots the operational stack, records an `active_stack_finalized` SQLite event, clears projection, and keeps context `WakeArchived` semantics computed from the post-archive semantic stack rather than a hard-coded empty list.

## Done

- Imported `finalize_active_stack_projection` into `novaic-cortex/novaic_cortex/api.py`.
- Added archive helpers for stack scope IDs, post-archive semantic stack calculation, deterministic finalize idempotency keys, and live archive finalization.
- Root archive now snapshots active stack and finalizes operational active-stack projection before filesystem archive.
- Wake child archive now snapshots active stack, appends the semantic `WakeArchived` event, records the operational finalize event, clears projection, and then archives/auto-closes children.
- Already-archived idempotent retry paths return compatible responses without appending conflicting duplicate finalize/context events.
- Added tests for root archive finalize and wake archive with an open child skill plus retry idempotency.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_context_event_api_lifecycle.py novaic-cortex/tests/test_context_event_write_authority.py novaic-cortex/tests/test_active_stack_projection.py`
  - Passed: 21 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/active_stack_projection.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
  - Passed.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 445 tests.
- Static search confirmed live `api.py` no longer hard-codes `remaining_stack=[]` for archive authority; remaining matches are test expectations.

## Known Gaps

- P029 still needs to perform the dedicated finalize residue check and may add more empty/non-empty archive verification if the parent check finds gaps.
- Operational finalize happens before filesystem archive completion. This preserves retry event idempotency but is not a cross-store atomic transaction.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
