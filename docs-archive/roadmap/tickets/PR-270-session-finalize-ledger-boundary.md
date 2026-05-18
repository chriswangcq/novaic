# PR-270 — Session Finalize Ledger Boundary

Status: Closed

## Goal

Move `session_finalize_rejected` / `session_finalized` event writing and the accepted finalize state transition (`ending` -> `no_active`) behind `SessionLedgerRepository`.

## Why

`session_ended()` should decide whether a finalize is accepted and then orchestrate restart/close behavior. It should not own the durable ledger payload shape, idempotency keys, or state mutation sequence for the finalize fact.

## Scope

- Add ledger methods for rejected and accepted finalize facts.
- Preserve pure `decide_session_finalize()` as the only source of accept/reject behavior.
- Update `SessionRepository.session_ended()` to delegate ledger writes.
- Add tests proving event payloads, state mutation, idempotency shape, and source-residue removal.

## Non-Goals

- Do not change finalize validation requirements.
- Do not change pending restart behavior.
- Do not change the pure FSM decision matrix.

## Acceptance Criteria

- `SessionRepository` no longer contains `event_type="session_finalize_rejected"` or `event_type="session_finalized"`.
- Accepted finalize event and ending/no_active state mutation are written by `SessionLedgerRepository`.
- Rejected finalize event is written by `SessionLedgerRepository`.
- Existing finalize ownership and pure FSM tests pass.
- Full `novaic-agent-runtime` test suite passes.

## Verification

- `pytest tests/test_pr270_session_finalize_ledger_boundary.py tests/test_pr254_finalize_ownership.py tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr241_pending_inbox_projection.py tests/test_pr243_inbox_restart_cutover.py`
- `pytest`
- `git diff --check`

## Closure Notes

- Added `SessionLedgerRepository.record_session_finalize_rejected()` and `record_session_finalized()`.
- Moved finalize event payloads, idempotency keys, and accepted finalize `ending -> no_active` state mutation into the ledger adapter.
- Updated `SessionRepository.session_ended()` to call ledger methods after the pure FSM decision.
- Added PR-270 tests for rejected finalize, accepted finalize, idempotency, state clearing, and source-residue guard.
- Verified targeted suite: 15 passed.
- Verified full runtime suite: 310 passed.
- Verified `git diff --check`: clean.
