# PR-252 Reliable Evolution FSM-07A Session State SSOT Cutover

Status: `[x]` deployed and closed

## Goal

Make `tq_session_state` the authoritative session state record. Keep
`tq_active_sessions` only as a compatibility view/cache during transition, or
remove live reads if safe.

## Phase Ledger

```text
Phase: FSM-07A session_state SSOT cutover
Subject: active/no_active/recovering session authority
Old source of truth: tq_active_sessions active pointer
New source of truth: tq_session_state
Input events: input_received, dispatch_saga_started, session_restarted, session_closed, session_suspected_dead
Decision function: current dispatch decision fed from session_state snapshot
State transition: all active/no_active changes upsert tq_session_state first
Outbox effects: unchanged from PR-251
Observation events: active_sessions compatibility drift
Generation/idempotency key: generation from tq_session_state
Shadow drift metric: active_sessions cache equals session_state active projection
Cutover switch: none
Rollback path: revert PR-252
Legacy deletion condition: no code path reads tq_active_sessions for routing
Tests: dispatch routes from session_state; active_sessions cache drift guarded; rebuild restores from sagas into state
Docs/guards to update: architecture cleanup table
```

## Small Tickets

- [x] **FSM-07A-A Read path**: route active lookup through
  `SessionLedgerRepository.get_state()`.
- [x] **FSM-07A-B Write path**: make state writes first-class for active,
  no_active, suspected_dead, and restarting transitions.
- [x] **FSM-07A-C Compatibility cache**: update or remove `tq_active_sessions`
  only as derived cache, with drift diagnostics.
- [x] **FSM-07A-D Rebuild**: rebuild `tq_session_state` from running sagas on
  boot; active cache can be repopulated from state.
- [x] **FSM-07A-E Tests/guards**: prove stale `tq_active_sessions` cannot drive
  routing when `session_state` disagrees.

## Explicit Dependency Boundary Review

The session state snapshot must be read once at the repository boundary and
passed to decision logic. Pure decision code must not read DB directly.

## Verification

- `pytest tests/test_pr252_session_state_ssot.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Local pass:

- `dispatch()` reads active routing state from `tq_session_state`, not
  `tq_active_sessions`.
- `SessionOutboxDispatcher.create_wake_saga` uses `tq_session_state` to detect
  the active winner and rewrites `tq_active_sessions` only as a derived cache.
- `session_ended()` clears active state before restart planning, so restart
  wake creation cannot race against the ended wake's stale state.
- `rebuild()` resets stale active state and reconstructs both session state and
  the compatibility cache from running/launched/pending sagas.
- Diagnostics `get_active_session()` / `list_active_sessions()` now project
  from `tq_session_state`.

Verification run:

- `python -m py_compile queue_service/session_outbox.py queue_service/session_repo.py tests/test_pr252_session_state_ssot.py`
- `pytest tests/test_pr252_session_state_ssot.py -q`
- `pytest tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr235_session_ledger.py tests/test_pr236_session_fsm_decision.py tests/test_pr237_session_outbox_observe.py tests/test_pr239_append_only_inbox.py tests/test_pr240_input_consumption.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr252_session_state_ssot.py -q`

Full suite passes locally.

Deployment closure:

- `./deploy runtime` completed successfully on 2026-05-06.
- `./deploy status` showed api services online on ports 19900, 19999, 19998,
  19993, 19997, 19995, and 19996, with 8 worker processes and relay active.

## Rollback

Revert PR-252. `tq_active_sessions` becomes routing authority again.
