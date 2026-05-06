# PR-248 Reliable Evolution FSM-06D Attach Input Outbox Cutover

Status: `[x]`

## Goal

Move active `session.attach_input` publishing from `SessionRepository` direct
`TaskQueue.publish` into the durable session outbox. PR-237 recorded attach
effects as observe-only ledger rows; PR-238 added generation checks. This ticket
turns the attach effect into the current publish path and deletes the direct
publish helper so future edits cannot bypass the outbox account.

## Phase Ledger

```text
Phase: FSM-06D attach input outbox cutover
Subject: active wake input attachment side effect
Old source of truth: SessionRepository._publish_attach_input_task direct TaskQueue.publish
New source of truth: tq_session_outbox publish_attach_input effect
Input events: input_received(user_message / im_message)
Decision function: SessionRepository active-session dispatch decision appends outbox effect
State transition: active + attachable input -> active(same generation)
Outbox effects: publish_attach_input -> TaskTopics.SESSION_ATTACH_INPUT
Observation events: dispatch_attached_to_active, dispatch_race_attached_to_active, input_consumed, outbox status
Generation/idempotency key: session-attach-input:{explicit idempotency_key or agent:subagent:scope:message_ids}
Shadow drift metric: no direct session.attach_input publish outside SessionOutboxDispatcher
Cutover switch: none; direct attach publish method is deleted
Rollback path: revert PR-248 after PR-247
Legacy deletion condition: outbox dispatcher tests pass and direct attach publish guard is green
Tests: attach outbox publishes task; failure leaves retryable outbox; direct method removed; existing active inbox behavior preserved
Docs/guards to update: ticket index, architecture implementation record, direct publish guard
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Add `publish_attach_input` support to `SessionOutboxDispatcher`.
- Active-session attach and race-attach branches append a durable outbox effect
  before publish.
- Publish is executed by the outbox dispatcher after the state/outbox write,
  preserving the existing user-facing `task_id` in the dispatch result.
- Delete `SessionRepository._publish_attach_input_task`.

## Out Of Scope

- Do not cut over wake saga creation in this ticket.
- Do not add a separate long-running outbox worker process yet.
- Do not make `tq_session_state` the sole active-session authority yet.
- Do not change `session.attach_input` handler generation checks.

## Small Tickets

- [x] **FSM-06D-A Dispatcher support**: add one-effect publish/ack helpers and
  `publish_attach_input` payload validation.
- [x] **FSM-06D-B Dispatch cutover**: active attach branches append the durable
  effect, publish through dispatcher, and keep input consumption explicit.
- [x] **FSM-06D-C Delete direct attach publish**: remove the old helper and add
  a guard scan/test against direct `TaskTopics.SESSION_ATTACH_INPUT` publish.
- [x] **FSM-06D-D Tests and docs**: cover success, failure/retry durability,
  existing active inbox behavior, and update architecture/ticket ledger.

## Explicit Dependency Boundary Review

- The attach decision remains explicit: active session snapshot, trigger type,
  message ids, session generation, and idempotency key are all inputs.
- The dispatcher is the imperative boundary: it reads outbox rows and calls
  `TaskQueue.publish` with an explicit payload.
- Unit tests inject clock, ID providers, and fake queues; no hidden time/id/env
  reads are allowed in the decision path.

## Legacy Cleanup Ledger

Delete in this ticket:

- `SessionRepository._publish_attach_input_task`.
- Direct `TaskQueue.publish(TaskTopics.SESSION_ATTACH_INPUT, ...)` from
  `SessionRepository`.
- Observe-only attach outbox idempotency key tied to an already published
  `task_id`.

Keep for later:

- Direct wake saga creation until wake saga outbox cutover.
- `tq_active_sessions` live active pointer until state cutover.
- Manual/immediate outbox drain until a durable outbox worker ticket exists.

## Verification

- `python -m py_compile queue_service/session_outbox.py queue_service/session_ledger.py queue_service/session_repo.py tests/test_pr248_attach_outbox_cutover.py`
- `pytest tests/test_pr248_attach_outbox_cutover.py tests/test_pr237_session_outbox_observe.py tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py -q`
- `pytest -q`
- `git diff --check`
- Guard scan: no runtime code publishes `TaskTopics.SESSION_ATTACH_INPUT`
  outside `queue_service/session_outbox.py`.

## Review Result

Closed.

- `SessionOutboxDispatcher` now supports `publish_attach_input` effects and
  has a single-row `publish_effect(outbox_id)` helper for synchronous
  coordinator cutovers.
- Active attach and race-attach write a durable outbox row before publishing;
  `dispatch()` keeps returning `task_id` on successful immediate publish.
- If immediate publish fails, the outbox row remains `pending` with
  attempts/error and the input is consumed because the durable outbox has taken
  ownership of delivery.
- `SessionRepository._publish_attach_input_task` and direct
  `TaskTopics.SESSION_ATTACH_INPUT` publish from the coordinator are deleted.

Verification passed:

- `python -m py_compile queue_service/session_outbox.py queue_service/session_ledger.py queue_service/session_repo.py tests/test_pr248_attach_outbox_cutover.py`
- `pytest tests/test_pr248_attach_outbox_cutover.py tests/test_pr237_session_outbox_observe.py tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr247_recovery_outbox_cutover.py -q`
- `pytest -q`

Guard evidence:

- `rg -n "SESSION_ATTACH_INPUT|session\\.attach_input|_publish_attach_input_task|publish_attach_input" queue_service task_queue tests -g '*.py'`
  shows publish of `TaskTopics.SESSION_ATTACH_INPUT` only in
  `queue_service/session_outbox.py`; remaining runtime references are the topic
  constant and handler.

## Rollback

Revert PR-248 to restore direct attach publish. PR-247 recovery outbox cutover
and prior inbox/generation work remain separate rollback decisions.
