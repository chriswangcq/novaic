# PR-264 Session Finalize FSM Boundary

Status: Closed

## Goal

Move session finalize accept/reject decisions into the pure session FSM layer so
`SessionRepository.session_ended()` no longer owns generation/scope mismatch
branch logic.

## Scope

- Add a pure finalize decision API to `queue_service.session_fsm`.
- Model finalize as an explicit state/event decision using the generic FSM
  substrate.
- Keep current rejection payloads and idempotency keys stable.
- Route `SessionRepository.session_ended()` through the pure decision.
- Add table-driven tests for finalize accept/reject cases and guard tests that
  mismatch branch construction does not reappear in the repository.

## Out Of Scope

- Restart saga creation and durable outbox remain in `SessionRepository` for now.
- Pending projection already moved in PR-263.
- DB schema changes are not needed.

## Small Tickets

- [x] **FSM-264-A Pure finalize decision**: add `decide_session_finalize()`.
- [x] **FSM-264-B Repository cutover**: use the pure decision in
  `session_ended()`.
- [x] **FSM-264-C Tests/residue**: pin reject payloads, accept generation, and
  repo residue guard.
- [x] **FSM-264-D Verification**: run targeted plus full runtime tests.

## Verification

- `pytest tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr254_finalize_ownership.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr245_suspected_dead_recovery.py`
- Full runtime `pytest`.

## Review Result

Pass. `SessionRepository.session_ended()` now consumes the pure
`decide_session_finalize()` decision for generation/scope mismatch handling.
Existing finalize ownership tests still pass, and the repo no longer builds the
rejection payload shapes itself.
