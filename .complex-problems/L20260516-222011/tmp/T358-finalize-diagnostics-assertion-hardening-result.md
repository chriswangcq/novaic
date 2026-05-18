# Finalize Diagnostics Assertion Hardening Result

## Summary

Hardened queue session finalize ownership tests so valid close diagnostics and stale finalize rejection diagnostics are asserted as explicit, generation-bound metadata rather than loosely inferred state.

## Done

- Added `_events_of_type` helper in `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py` for precise ledger event assertions.
- Strengthened valid finalize coverage to assert the `session_finalized` event generation and exact payload.
- Strengthened valid finalize coverage to assert the `session_closed` event generation and metadata exactly match the explicit finalize metadata.
- Strengthened stale generation rejection coverage to assert the active session remains unchanged, no `session_finalized` event is emitted, and `session_finalize_rejected` records the stale finalize's own reason, generation, scope, and remaining stack.
- Strengthened stale scope rejection coverage to assert the active session remains unchanged, no `session_finalized` event is emitted, and `session_finalize_rejected` records the stale scope finalize metadata.

## Verification

- `python3 -m py_compile queue_service/session_repo.py queue_service/session_ledger.py queue_service/session_fsm.py tests/test_pr254_finalize_ownership.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr233_active_inbox_dispatch.py`
- Result: `20 passed in 0.27s`
- Residue search: `rg -n "finalize_metadata|record_session_finalized|record_session_finalize_rejected|remaining_stack|finalize_reason" queue_service/session_repo.py queue_service/session_ledger.py queue_service/session_fsm.py tests/test_pr254_finalize_ownership.py`

## Known Gaps

- None for this ticket. The remaining Cortex archive diagnostics work is tracked separately under the parent finalize diagnostics problem.

## Artifacts

- Changed test: `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- Ticket: `.complex-problems/L20260516-222011/tmp/P370-finalize-diagnostics-assertion-hardening-ticket.md`
