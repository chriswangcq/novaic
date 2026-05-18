# PR-247 Reliable Evolution FSM-06C Recovery Archive Outbox Cutover

Status: `[x]`

## Goal

Move recovery structural archive (`cortex.scope_end`) from a direct publish
side effect into the durable session outbox. PR-245 made recovery event-driven;
PR-246 deleted the old marker source. This ticket removes the remaining direct
publish branch for recovery archive tasks.

## Phase Ledger

```text
Phase: FSM-06C recovery archive outbox cutover
Subject: recovery structural archive side effect
Old source of truth: SagaOrchestrator.queue_recovery_scope_end_task direct TaskQueue.publish
New source of truth: tq_session_outbox recovery_archive_scope effect
Input events: session_suspected_dead, input_received
Decision function: SessionRepository dispatch recovery decision appends outbox effect
State transition: suspected-dead observed -> recovered wake active(new generation)
Outbox effects: recovery_archive_scope -> TaskTopics.CORTEX_SCOPE_END
Observation events: session_suspected_dead_observed, dispatch_saga_started, input_consumed, outbox status
Generation/idempotency key: recovery-cortex-scope-end:{failed_scope_id}
Shadow drift metric: no direct recovery archive publish outside outbox dispatcher
Cutover switch: none; recovery archive direct publish method is deleted
Rollback path: revert PR-247 after PR-246
Legacy deletion condition: outbox dispatcher tests pass and direct recovery publish guard is green
Tests: pending outbox drains to task; publish failure keeps retryable outbox; direct method removed
Docs/guards to update: ticket index, architecture implementation record, direct publish guard
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Add a narrow session outbox dispatcher for `recovery_archive_scope` effects.
- On recovery dispatch, append the archive effect to `tq_session_outbox` instead
  of calling `TaskQueue.publish` directly.
- Drain pending recovery archive effects after the dispatch transaction. If the
  publish fails, the effect remains durable and retryable.
- Remove `SagaOrchestrator.queue_recovery_scope_end_task`.

## Out Of Scope

- Do not cut over wake saga creation or active attach publish in this ticket.
- Do not introduce a separate long-running outbox worker process yet.
- Do not change finalize ownership or `tq_active_sessions` live authority.

## Small Tickets

- [x] **FSM-06C-A Outbox dispatcher**: add claim/publish/ack helpers for
  `recovery_archive_scope` effects.
- [x] **FSM-06C-B Dispatch cutover**: recovery dispatch writes a durable outbox
  effect and drains it after commit instead of direct publish.
- [x] **FSM-06C-C Delete direct recovery publish**: remove
  `queue_recovery_scope_end_task` and guard against reintroduction.
- [x] **FSM-06C-D Tests and docs**: cover success, failure/retry durability, and
  update architecture/ticket ledger.

## Explicit Dependency Boundary Review

- The recovery archive decision is explicit data in the outbox payload.
- The dispatcher is an imperative boundary: it reads durable outbox rows and
  calls `TaskQueue.publish` with an explicit payload and idempotency key.
- Unit tests inject clock, IDs, and fake failing queues to make retry behavior
  deterministic.

## Legacy Cleanup Ledger

Delete in this ticket:

- `SagaOrchestrator.queue_recovery_scope_end_task`.
- Direct recovery archive publish call from `SessionRepository.dispatch()`.

Keep for later:

- Direct wake saga creation publish until full outbox cutover.
- Direct active attach publish until full outbox cutover.
- `tq_active_sessions` live active pointer until state cutover.

## Verification

- `pytest tests/test_pr247_recovery_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py -q`
- `pytest -q`
- `git diff --check`
- Guard scan: no runtime code calls `queue_recovery_scope_end_task` or publishes
  `TaskTopics.CORTEX_SCOPE_END` for recovery outside the outbox dispatcher.

## Review Result

Closed.

- Recovery dispatch now appends `recovery_archive_scope` to
  `tq_session_outbox` and drains it through `SessionOutboxDispatcher`.
- `SagaOrchestrator.queue_recovery_scope_end_task` and the direct recovery
  archive publish call are deleted.
- Publish failure leaves the outbox row `pending` with attempt/error state; a
  later dispatcher drain replays the same idempotency key and marks the row
  `published`.

Verification passed:

- `python -m py_compile tests/test_pr247_recovery_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py queue_service/session_outbox.py queue_service/session_ledger.py queue_service/session_repo.py queue_service/saga_repo.py`
- `pytest tests/test_pr247_recovery_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py -q`
- `pytest -q`

Guard evidence:

- `rg -n "queue_recovery_scope_end_task|CORTEX_SCOPE_END|recovery_archive_scope|SessionOutboxDispatcher" queue_service task_queue`
  shows recovery archive publish only in `queue_service/session_outbox.py`;
  remaining `CORTEX_SCOPE_END` references are the topic constant, handler, and
  wake-finalize DAG definition.

## Rollback

Revert PR-247 to restore direct recovery archive publish. The durable suspected
dead event path from PR-245 and marker deletion from PR-246 remain separate
rollback decisions.
