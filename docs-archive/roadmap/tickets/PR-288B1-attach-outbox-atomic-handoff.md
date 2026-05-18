# PR-288B1 — Attach Outbox Atomic Handoff

Status: Closed

## Goal

Make active-input attach a single durable handoff: the attach transition,
attach outbox row, and input-consumed accounting must be written atomically
before any publish attempt.

## Scope

- Extend the ledger transition boundary so it can consume specific input events
  in the same transaction as transition/outbox persistence.
- Remove repository-side post-publish input-consumption writes for attach.
- Keep publish retry behavior unchanged: once input is handed to durable outbox,
  the outbox owns delivery.
- Add residue/test coverage so future code does not reintroduce split
  transition/outbox/consume writes.

## Dependencies

- PR-248 attach outbox cutover.
- PR-288A wake-created observed handler.
- PR-290A/B critical write hardening.

## Acceptance Criteria

- Attach transition, attach outbox row, and input-consumed event are committed
  together.
- A failed attach publish leaves a retryable outbox row but does not leave the
  input pending for duplicate dispatch.
- `SessionRepository` no longer has a separate input-consumption helper.
- Full runtime suite passes.

## Verification

- Attach outbox tests.
- Input consumption tests.
- Residue guard tests.
- Full runtime suite.

## Closure Notes

- Extended `SessionLedgerRepository.record_transition` with optional explicit
  input-consumption fields so transition, outbox, and input-consumed accounting
  can be committed together.
- `SessionRepository` no longer has a separate
  `_mark_input_events_consumed_after_transaction` helper for attach.
- Active attach now durably hands input to the attach outbox before publish; a
  publish failure leaves a retryable outbox row and no duplicate pending inbox
  input.
- Verified by targeted attach/input/residue tests:
  `pytest tests/test_pr248_attach_outbox_cutover.py tests/test_pr240_input_consumption.py tests/test_pr268_session_input_ledger_boundary.py tests/test_pr273_session_harness_final_residue_guard.py tests/test_pr281_session_outbox_wrapper_boundary.py`
  -> 15 passed.
