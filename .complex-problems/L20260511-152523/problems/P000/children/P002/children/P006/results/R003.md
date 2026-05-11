# Wake finalize compensation repair result

## Summary

Repaired wake-finalize compensation so failed wake/think/actions sagas preserve the root/path/session context required for cleanup and `session_ended`.

## Done

- Updated `_build_wake_finalize_compensation_effect` to preserve explicit context keys:
  - `agent_root_scope_id`
  - `wake_scope_path`
  - `session_generation`
  - `remaining_stack`
  - `stack_known_at_finalize`
  - `stack_depth_at_finalize`
  - `round_num`
- Extended durable saga outbox regression tests to verify both pending compensation effect and published `wake_finalize` saga keep those fields.
- Added assertions that preserved compensation context drives `_build_cortex_scope_end_payload` and `_build_session_ended_payload` correctly.

## Verification

- `pytest -q tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr254_finalize_ownership.py` in `novaic-agent-runtime`: `10 passed`.
- `pytest -q tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py` in `novaic-agent-runtime`: `12 passed`.

## Known Gaps

- None for compensation-context preservation. The full repair still needs parent aggregation, broader tests, deployment, and live stuck-session recovery verification.

## Artifacts

- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/tests/test_pr311_saga_compensation_outbox_cutover.py`
