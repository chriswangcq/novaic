# PR-237 Reliable Evolution FSM-03A Durable Outbox Observe

Status: `[x]`

## Goal

Start the durable side-effect ledger for Queue session harness by recording
outbox effects beside the existing live side effects. This PR must not route
publishing through the outbox yet.

## Scope

- Runtime only: `novaic-agent-runtime`.
- Record observe-only outbox effects for:
  - wake saga creation
  - active input attach task publish
  - pending-trigger restart saga creation
- Keep direct `SagaOrchestrator.create()` and `TaskQueue.publish()` as the live path.
- Add tests proving outbox effects are recorded while old side effects still happen.

## Out Of Scope

- Do not implement the outbox worker.
- Do not cut over attach or wake creation to the outbox.
- Do not delete direct publish paths.
- Do not add dead-letter or ack semantics yet.

## Small Tickets

- [x] **FSM-03A-A Effect payloads**: add observe-only `create_wake_saga` and `publish_attach_input` effect records.
- [x] **FSM-03A-B Idempotency keys**: make shadow effects idempotent by the already-created saga/task id.
- [x] **FSM-03A-C Live path proof**: assert `tq_tasks` still receives direct `session.attach_input`.
- [x] **FSM-03A-D Restart proof**: assert pending-trigger restart still uses the legacy pending table while recording an outbox effect.
- [x] **FSM-03A-E Tests**: add PR-237 tests and re-run runtime suite.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr237_session_outbox_observe.py`

## Legacy Cleanup Ledger

Keep these deliberately for now:

- Direct `SagaOrchestrator.create()` for wake/restart.
- Direct `TaskQueue.publish()` for `session.attach_input`.
- `tq_session_outbox.status='pending'` effects are not consumed yet.

Deletion criteria:

- Delete none in PR-237.
- Direct publish/create can only be removed after a later outbox worker PR proves retry, ack, idempotency, and backlog observability.

## Verification

- `pytest tests/test_pr237_session_outbox_observe.py tests/test_pr236_session_fsm_shadow_decision.py tests/test_pr235_session_ledger_shadow.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. Durable outbox effects are now visible and idempotent, but live side
effects are still performed by the old path. This keeps the migration
observable without creating a second active publisher.

## Rollback

Revert this PR. Existing live side effects are unchanged; outbox rows are
additive shadow data.
