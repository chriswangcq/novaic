# Check: Attach repository payload generation audit

## Summary

Success. The one-go result found a real stale-scope attach race, fixed it at the repository boundary, deleted the stale `active_generation(...)` fallback, and added focused regression coverage. The result is not just an inventory; it closes the concrete repository-side failure mode.

## Evidence

- R315 maps repository attach creation and expected generation computation.
- `session_repo.py::_record_attach_request_after_transaction(...)` now re-reads current active state inside the same transaction that records attach outbox.
- If current active saga/scope differs from the attach request, the input is buffered and no attach outbox is created.
- `SessionLedgerRepository.active_generation(...)` and `SessionRepository._active_session_generation_after_transaction(...)` were removed.
- Regression test `test_attach_request_buffers_if_active_session_changes_before_record` proves the stale request path buffers input, creates no attach outbox, and leaves the input unconsumed.

## Criteria Map

- Attach request creation and expected generation paths mapped: satisfied by R315.
- `active_generation(...)` scope mismatch behavior classified: satisfied; it was dangerous residue and removed.
- Repository-side stale-scope attach behavior tested/fixed: satisfied by code change and regression test.
- Result identifies downstream checks still needed: satisfied; P331/P332/P333 remain for outbox/runtime/end-to-end validation.

## Execution Map

- T320 executed one bounded implementation/audit pass.
- Changed `session_repo.py`, `session_ledger.py`, and `test_pr248_attach_outbox_cutover.py`.

## Stress Test

- Simulated the race where an attach request is based on old `saga/scope`, then session state advances to a new `saga/scope` before attach recording.
- Verified repository now buffers instead of emitting old-scope attach outbox.
- Guarded against stale helper return by checking no `active_generation(...)` or `_active_session_generation_after_transaction` remains.

## Residual Risk

- Non-blocking for P330: outbox worker delivery, runtime handler enforcement, and broader attach regression are intentionally covered by P331, P332, and P333.

## Result IDs

- R315
