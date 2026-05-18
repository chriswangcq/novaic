# Finalize Diagnostics Aggregate Verification Result

## Summary

Completed aggregate finalize diagnostics verification and fixed one additional boundary gap found during residue review: `SessionRepository.session_ended(...)` now rejects bool generation instead of allowing `int(True) == 1`.

## Changes Made

- Added `_require_positive_generation(...)` in `queue_service/session_repo.py`.
- Updated `session_ended(...)` to use the helper for explicit positive generation validation.
- Added a regression assertion to `tests/test_pr254_finalize_ownership.py` proving repo-level bool generation is rejected.

## Evidence

- Runtime compile: `python3 -m py_compile queue_service/session_repo.py task_queue/handlers/session_handlers.py task_queue/sagas/wake_finalize.py task_queue/handlers/cortex_handlers.py task_queue/utils/cortex_bridge.py`
- Runtime focused finalize/recovery/compensation suite: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_finalize_summary_boundary.py tests/test_scope_end_environment_notifications.py tests/test_pr266_session_recovery_boundary.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr233_active_inbox_dispatch.py` -> 57 passed.
- Cortex archive/context suite: `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_pr74_scope_summary_contract.py tests/test_context_event_projection.py tests/test_context_event_write_authority.py` -> 55 passed.

## Residue Review

- `ended_at`, `utc_now`, and `uuid4` did not appear in the focused finalize/archive files scanned.
- `time.time` appears only in `CortexBridge.from_config(...)` as an injected clock default for the adapter, not as finalize generation/diagnostics source.
- Remaining generation reads in `session_repo.py` are session ledger generation allocation or attach expected-generation validation, not Cortex archive diagnostic synthesis.
- Runtime finalize/archive handlers require explicit `finalize_reason`, positive generation, and object-shaped `remaining_stack`.

## Residual Note

No follow-up is needed for P369.
