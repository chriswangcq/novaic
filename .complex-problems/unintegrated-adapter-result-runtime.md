# Queue FSM Saga session adapter audit result

## Summary

The session coordinator is substantially on the new FSM/session-ledger/outbox path: `SessionRepository` injects clock/scope-id dependencies, uses `tq_session_state` through `SessionLedgerRepository`, and records wake creation through session outbox before `SessionOutboxDispatcher` creates the saga. The main remaining similar integration gap is a live generic saga-creation surface: `saga.trigger` and `/api/queue/sagas/create` can still create arbitrary saga types, so the codebase has not physically prevented old-style direct `subagent_wake` creation outside the session outbox.

## Done

Inspected session and saga coordination:

- `queue_service/session_repo.py` requires explicit `clock`, `scope_id_provider`, `SessionLedgerRepository`, and `SessionOutboxDispatcher`.
- `dispatch()` appends input events, consults `decide_session_dispatch`, records transitions in `tq_session_state`/session ledger, and stores `create_wake_saga` as durable session outbox effect.
- `SessionOutboxDispatcher._publish_create_wake_saga()` is the expected imperative boundary that calls `saga_orchestrator.create()` after reading a durable outbox row.
- `SessionObservedEventHandler.apply_wake_created()` generation-checks the observation before recording active state.
- `session_ended()` requires `finalize_reason`, `generation`, and `remaining_stack`, then uses `decide_session_finalize`.
- `SagaOrchestrator.mark_failed()` now persists compensation intent as saga outbox effects, and the compensation payload preserves root/path/generation/stack metadata.

Confirmed remaining gap:

- `queue_service/routes.py` still exposes `POST /api/queue/sagas/create`, which directly calls `orchestrator.create()`.
- `task_queue/handlers/saga_handlers.py` registers `SagaTopics.SAGA_TRIGGER` and calls `saga_client.create(...)` for whatever `saga_type` is in the task payload.
- `task_queue/topics.py` keeps `SagaTopics.SAGA_TRIGGER` in the control pool.
- Current saga definitions legitimately use `SAGA_TRIGGER` for child `react_think`, `react_actions`, and `wake_finalize` creation, but the handler does not restrict `subagent_wake`.
- Therefore an old or accidental publisher could still create `subagent_wake` without going through `SessionRepository.dispatch()` and session outbox, bypassing inbox buffering, generation state, and observed wake-created handling.

Non-issues / already clean:

- `tq_active_sessions` did not appear in current production queue/session source; residue guards already assert it is absent from session harness files.
- `SessionRepository` no longer calls `.orchestrator.create()` directly.
- `SessionRepository` no longer owns low-level outbox append/publish helper wrappers; session outbox is a separate boundary.
- The environment aggregation config in `novaic-business/business/subscribers/dispatch_subscriber.py` has already been moved behind `load_im_aggregation_config_from_env()` and constructor config, so the earlier implicit-env finding appears fixed.

## Verification

- Source search:
  - `rg -n "tq_active_sessions|tq_session_state|SessionRepository|SagaOrchestrator|saga_orchestrator.create|SAGA_TRIGGER|/sagas/create|generation|outbox" ...`
- Code inspection:
  - `novaic-agent-runtime/queue_service/session_repo.py`
  - `novaic-agent-runtime/queue_service/session_outbox.py`
  - `novaic-agent-runtime/queue_service/session_observed_events.py`
  - `novaic-agent-runtime/queue_service/saga_repo.py`
  - `novaic-agent-runtime/task_queue/handlers/saga_handlers.py`
  - `novaic-agent-runtime/task_queue/sagas/react_think.py`
  - `novaic-agent-runtime/task_queue/sagas/react_actions.py`
  - `novaic-agent-runtime/task_queue/sagas/subagent_wake.py`
- Existing guard evidence:
  - `novaic-agent-runtime/tests/test_pr273_session_harness_final_residue_guard.py`

## Known Gaps

- High-priority follow-up: restrict `SagaTopics.SAGA_TRIGGER` and `/sagas/create` so `subagent_wake` cannot be created except through `SessionOutboxDispatcher.CREATE_WAKE_SAGA`. A narrower option is to add an explicit allowlist for saga-trigger-created child saga types (`react_think`, `react_actions`, `wake_finalize`) and require session outbox provenance for `subagent_wake`.
- Medium-priority hardening: `SessionRepository` remains a thick coordinator with imperative branches around pure FSM decisions. It appears functionally clean, but the “all dispatch branches are pure FSM decision + effect plan” ideal is not fully physical yet.

## Artifacts

- `novaic-agent-runtime/queue_service/routes.py:361`
- `novaic-agent-runtime/task_queue/handlers/saga_handlers.py:34`
- `novaic-agent-runtime/task_queue/sagas/subagent_wake.py:109`
- `novaic-agent-runtime/queue_service/session_outbox.py:188`
- `novaic-agent-runtime/queue_service/session_repo.py:69`
- `novaic-agent-runtime/tests/test_pr273_session_harness_final_residue_guard.py:50`
