# PR-262 Session Transition Ledger Boundary

Status: Closed

## Goal

Move session transition write accounting out of `SessionRepository` and into the
store-backed `SessionLedgerRepository` adapter.

## Scope

- Add a ledger method that records one transition event, materialized state, and
  durable outbox effects as a single boundary operation.
- Move session generation calculation helpers from `SessionRepository` to the
  ledger adapter.
- Keep persisted event keys and idempotency keys stable.
- Add guard tests that `SessionRepository` no longer directly calls
  `append_event`/`upsert_state`/`append_outbox` for transition writes.

## Out Of Scope

- Full finalize/recovery reducer unification remains a later PR.
- DB schema changes are not needed.

## Small Tickets

- [x] **FSM-262-A Ledger API**: add `record_transition()` and generation helpers.
- [x] **FSM-262-B Repository cutover**: route transition writes through the ledger
  boundary.
- [x] **FSM-262-C Residue deletion**: remove repository transition write helper
  and generation helper.
- [x] **FSM-262-D Tests/review**: run targeted tests and residue scans.

## Verification

- `pytest tests/test_pr260_session_harness_generic_fsm_cutover.py tests/test_pr235_session_ledger.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr253_dispatch_pure_fsm_cutover.py tests/test_pr254_finalize_ownership.py tests/test_pr257_remove_active_sessions_table.py`
- Guard scan for `_write_session_event_and_state` and `_session_generation` in
  `queue_service/session_repo.py`.

## Review Result

Pass. `SessionRepository` no longer owns the transition write helper or session
generation helper; it delegates event/state/outbox accounting to
`SessionLedgerRepository.record_transition()`.
