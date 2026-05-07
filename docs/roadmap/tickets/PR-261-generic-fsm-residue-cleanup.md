# PR-261 Generic FSM Residue Cleanup

Status: Closed

## Goal

Delete stale session-specific FSM migration residue after the generic FSM store
is the only active path.

## Cleanup Checklist

- [x] Remove unused session ledger record shells made obsolete by the generic
  store adapter.
- [x] Remove historical "shadow" helper terminology from active runtime code
  while keeping persisted idempotency keys stable.
- [x] Preserve `self.orchestrator` because existing callers/tests observe it;
  do not delete active API surface as cleanup.
- [x] Add guard tests for deleted session ledger shells and unused orchestrator.
- [x] Keep historical ticket files as archaeology; active architecture/tickets
  now state the current generic FSM substrate.

## Verification

- `pytest tests/test_pr258_generic_fsm_substrate.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr260_session_harness_generic_fsm_cutover.py tests/test_pr261_generic_fsm_residue_cleanup.py tests/test_pr235_session_ledger.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr253_dispatch_pure_fsm_cutover.py tests/test_pr254_finalize_ownership.py tests/test_pr257_remove_active_sessions_table.py`

## Review Result

Pass. Deleted unused record shells and added tests that keep those residues from
returning. Kept `self.orchestrator` after full-suite review showed it is still
observable active surface, not safe residue.
