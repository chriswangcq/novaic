# PR-253 Reliable Evolution FSM-02B Dispatch Pure FSM Cutover

Status: `[x]` deployed and closed

## Goal

Make `queue_service.session_fsm.decide_session_dispatch()` the live dispatch
decision source. `SessionRepository.dispatch()` should assemble an explicit
snapshot, call the pure decision, and interpret returned effects.

## Phase Ledger

```text
Phase: FSM-02B dispatch pure FSM cutover
Subject: dispatch route selection
Old source of truth: imperative if/else branches in SessionRepository
New source of truth: SessionDispatchInput -> SessionDispatchDecision
Input events: input_received(...)
Decision function: decide_session_dispatch
State transition: interpreter applies decision
Outbox effects: create_wake_saga, publish_attach_input, recovery_archive_scope
Observation events: decision trace without legacy drift
Generation/idempotency key: explicit state snapshot generation
Shadow drift metric: removed; no dual decision after cutover
Cutover switch: none
Rollback path: revert PR-253
Legacy deletion condition: delete DispatchRoute/decide_dispatch_route usage from SessionRepository
Tests: pure FSM route table; repository invokes decision exactly from explicit snapshot
Docs/guards to update: architecture implementation record
```

## Small Tickets

- [x] **FSM-02B-A Snapshot assembler**: build a typed dispatch snapshot from
  explicit input event + `session_state`.
- [x] **FSM-02B-B Decision interpreter**: map pure actions to start/attach/buffer
  implementation paths.
- [x] **FSM-02B-C Remove legacy route branch**: remove `decide_dispatch_route`
  from `SessionRepository` live path.
- [x] **FSM-02B-D Tests/guards**: cover active attach, active buffer,
  no_active start, suspected_dead recovery.

## Explicit Dependency Boundary Review

The pure FSM accepts only explicit `SessionDispatchInput`; DB, time, ids, and
outbox publishing stay in repository/dispatcher adapters.

## Verification

- `pytest tests/test_pr253_dispatch_pure_fsm_cutover.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Local pass:

- `SessionRepository.dispatch()` assembles an explicit `SessionDispatchInput`
  from the current `tq_session_state` snapshot and metadata.
- Live attach/buffer/start decisions are interpreted from
  `decide_session_dispatch()`.
- `SessionRepository` no longer imports or calls legacy
  `decide_dispatch_route` / `DispatchRoute`.
- Existing suspected-dead recovery path continues to force no-active start
  through the pure FSM start decision.

Verification run:

- `python -m py_compile queue_service/session_repo.py tests/test_pr253_dispatch_pure_fsm_cutover.py`
- `pytest tests/test_pr253_dispatch_pure_fsm_cutover.py -q`
- `pytest tests/test_pr236_session_fsm_decision.py tests/test_pr253_dispatch_pure_fsm_cutover.py -q`
- `pytest tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr235_session_ledger.py tests/test_pr236_session_fsm_decision.py tests/test_pr237_session_outbox_observe.py tests/test_pr239_append_only_inbox.py tests/test_pr240_input_consumption.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr253_dispatch_pure_fsm_cutover.py -q`

Full suite passes locally.

Deployment closure:

- `./deploy runtime` completed successfully on 2026-05-06.
- `./deploy status` showed api services online on ports 19900, 19999, 19998,
  19993, 19997, 19995, and 19996, with 8 worker processes and relay active.

## Rollback

Revert PR-253. Legacy imperative branch selection returns.
