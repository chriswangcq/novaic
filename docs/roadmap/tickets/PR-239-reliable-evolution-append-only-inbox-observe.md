# PR-239 Reliable Evolution FSM-05A Append-only Inbox Observe

Status: `[x]`

## Goal

Start the inbox migration without changing live routing: every `SessionRepository.dispatch()`
input is recorded as an append-only `input_received` session event. This gives
the FSM a replayable input ledger before `tq_pending_triggers` becomes
non-authoritative.

## Scope

- Runtime only: `novaic-agent-runtime`.
- Record one shadow `input_received` event for every dispatch input.
- Preserve dispatch metadata and extracted `message_ids` in the event payload.
- Use dispatch idempotency keys, when present, to dedupe replay of the same
  logical input event.
- Keep existing live `pending_triggers`, direct attach, and wake creation
  behavior unchanged.
- Update existing shadow-ledger tests so they keep asserting result events
  without assuming input events do not exist.

## Out Of Scope

- Do not cut the live inbox source over from `tq_pending_triggers`.
- Do not delete `tq_pending_triggers`.
- Do not make `tq_session_state` authoritative yet.
- Do not introduce an outbox worker.
- Do not change LLM behavior or agent autonomy semantics.

## Small Tickets

- [x] **FSM-05A-A Append-only input event**: write `input_received` into
  `tq_session_events` at the dispatch boundary before legacy branching.
- [x] **FSM-05A-B Explicit input payload**: persist `trigger_type`,
  `message_ids`, and the original metadata snapshot in the event payload.
- [x] **FSM-05A-C Idempotent logical input**: use
  `shadow:input_received:{idempotency_key}` only when the caller supplied a
  dispatch idempotency key; otherwise append every non-idempotent dispatch.
- [x] **FSM-05A-D Preserve live pending path**: keep scheduled wakes buffered in
  legacy pending storage until the inbox cutover ticket.
- [x] **FSM-05A-E Tests**: prove every dispatch input is appended and repeated
  idempotent dispatches produce one logical input event.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr235_session_ledger_shadow.py`
- `novaic-agent-runtime/tests/test_pr236_session_fsm_shadow_decision.py`
- `novaic-agent-runtime/tests/test_pr239_append_only_inbox_observe.py`

## Explicit Dependency Boundary Review

Compliant for this observe step.

- The input event is produced at the repository boundary from explicit dispatch
  arguments: `agent_id`, `subagent_id`, `user_id`, `trigger_type`, `metadata`,
  `idempotency_key`, and injected clock output.
- The event id, clock, and ledger dependency remain injectable through
  `SessionLedgerRepository` and `SessionRepository`.
- No core FSM decision is changed; this ticket records the explicit input
  snapshot that later pure decisions will consume.

## Legacy Cleanup Ledger

Keep these deliberately for now:

- `tq_pending_triggers` remains the live pending store.
- Direct `TaskQueue.publish()` attach path remains live.
- Direct wake saga creation remains live.

Deletion criteria:

- `tq_pending_triggers` can only be retired after FSM-05B/05C proves ordered
  replay, pending recovery, and inbox cutover with tests.
- Direct publish removal waits for the durable outbox cutover.

## Verification

- `pytest tests/test_pr239_append_only_inbox_observe.py tests/test_pr238_generation_checked_attach.py tests/test_pr236_session_fsm_shadow_decision.py tests/test_pr235_session_ledger_shadow.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. The ticket adds a replayable input ledger while leaving the current live
routing path untouched. Existing shadow-ledger assertions were narrowed to
result events so the new input events do not weaken the previous tests.

## Rollback

Revert this PR. The additive event writes are observe-only; removing them
returns runtime behavior to PR-238 without schema rollback.
