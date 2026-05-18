# PR-260 Session Harness Generic FSM Cutover

Status: Closed

## Goal

Make Queue `SessionRepository` apply session transitions through the generic FSM
store and transition contract instead of bespoke transaction branches.

## Scope

- Dispatch: append input event, load current state, decide, persist state/effects.
- Finalize: append explicit finalize event with reason, generation, and remaining
  stack; let the FSM clear active state.
- Watchdog/recovery: watchdog appends suspected-dead events; recovery wake is a
  normal FSM decision.
- Attach: publish attach only from durable outbox with generation check.

## Cleanup Checklist

- [x] Delete direct `tq_session_state` SQL from `SessionRepository`; active
  state mutation now goes through the store-backed ledger adapter.
- [x] Delete old "shadow" helper naming from live code where it no longer describes
  behavior.
- [x] Keep durable idempotency key strings stable for production safety; only
  code helper/log names were cleaned.
- [x] Add guard tests for no direct session table SQL in `SessionRepository`.

## Verification

- `pytest tests/test_pr260_session_harness_generic_fsm_cutover.py tests/test_pr257_remove_active_sessions_table.py tests/test_pr254_finalize_ownership.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr253_dispatch_pure_fsm_cutover.py tests/test_pr259_generic_fsm_store_outbox.py`

## Review Result

Pass. `SessionRepository` no longer owns session-state table SQL and no longer
exposes stale `shadow_*` helper names. Dispatch decisions use the pure FSM core;
event/state/outbox table mechanics flow through `FsmSqliteStore`.
