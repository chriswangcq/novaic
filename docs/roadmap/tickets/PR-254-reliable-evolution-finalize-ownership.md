# PR-254 Reliable Evolution FSM-07B Finalize Ownership

Status: `[x]` deployed and closed

## Goal

Finalize must be an explicit session lifecycle event carrying `reason`,
`generation`, and `remaining_stack`. The session FSM owns active cleanup instead
of ad hoc scope_end/session_ended behavior.

## Phase Ledger

```text
Phase: FSM-07B finalize ownership
Subject: wake finalize and active cleanup
Old source of truth: wake_finalize/session_ended directly clears active pointer
New source of truth: finalize event interpreted by session coordinator/FSM
Input events: session_finalized(reason, generation, remaining_stack)
Decision function: finalize decision with explicit stack snapshot
State transition: active -> ending -> no_active or restart
Outbox effects: recovery_archive_scope, create_wake_saga restart if pending
Observation events: session_finalized, finalize_forced, finalize_rejected
Generation/idempotency key: finalize:{session_key}:{scope_id}:{generation}:{reason}
Shadow drift metric: no finalize without reason/generation/remaining_stack
Cutover switch: none
Rollback path: revert PR-254
Legacy deletion condition: session_ended handler cannot clear active without finalize event
Tests: natural finalize, forced finalize, non-empty stack archive, pending restart
Docs/guards to update: architecture invariants
```

## Small Tickets

- [x] **FSM-07B-A Payload contract**: require `finalize_reason`,
  `generation`, and `remaining_stack` or explicit unknown sentinel.
- [x] **FSM-07B-B Session event**: append `session_finalized` before clearing
  active state.
- [x] **FSM-07B-C Cleanup owner**: route active cleanup through session
  coordinator/FSM.
- [x] **FSM-07B-D Tests/guards**: prove missing finalize reason fails loudly and
  remaining stack is persisted.

## Explicit Dependency Boundary Review

Finalize decision must receive a stack snapshot from Cortex/tool boundary. It
must not rediscover current stack through hidden DB/file reads inside pure logic.

## Verification

- `pytest tests/test_pr254_finalize_ownership.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Local pass:

- `/api/queue/session-ended`, `TaskQueueClient.session_ended`, and
  `session.ended` worker handler now require `finalize_reason`, `generation`,
  and `remaining_stack`.
- `wake_finalize` builds an explicit finalize contract from saga context,
  including session generation and remaining stack snapshot.
- `SessionRepository.session_ended()` appends `session_finalized` before
  cleanup, transitions `active -> ending -> no_active`, and rejects stale
  finalize attempts on generation or scope mismatch without clearing active.
- Restart-after-finalize carries the finalize metadata into the new wake saga
  context.

Verification run:

- `python -m py_compile queue_service/session_repo.py queue_service/routes.py task_queue/client.py task_queue/handlers/session_handlers.py task_queue/sagas/wake_finalize.py task_queue/contracts/react_actions.py task_queue/contracts/react_think.py`
- `pytest tests/test_pr254_finalize_ownership.py -q`
- `pytest tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr235_session_ledger.py tests/test_pr236_session_fsm_decision.py tests/test_pr237_session_outbox_observe.py tests/test_pr238_generation_checked_attach.py tests/test_pr239_append_only_inbox.py tests/test_pr240_input_consumption.py tests/test_pr241_pending_inbox_projection.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr253_dispatch_pure_fsm_cutover.py tests/test_pr254_finalize_ownership.py tests/test_pr255_legacy_compat_cleanup.py tests/test_pr48_turn_finalizer.py tests/test_finalize_summary_boundary.py tests/test_pr234_repeated_scope_mismatch.py -q`

Full suite passes locally.

Deployment closure:

- `./deploy runtime` completed successfully on 2026-05-06.
- `./deploy status` showed api services online on ports 19900, 19999, 19998,
  19993, 19997, 19995, and 19996, with 8 worker processes and relay active.

## Rollback

Revert PR-254. Existing wake_finalize/session_ended cleanup path returns.
