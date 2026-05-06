# PR-240 Reliable Evolution FSM-05B Input Consumption Observe

Status: `[x]`

## Goal

Add observe-only consumption accounting for append-only input events. The system
should be able to tell which `input_received` events have already been handed to
a wake/attach/restart path and which remain unconsumed pending inbox.

## Scope

- Runtime only: `novaic-agent-runtime`.
- Add explicit ledger helpers for unconsumed input queries and consumed marking.
- Append `input_consumed` observation events for each consumed input event.
- Mark `input_received.consumed_at` as a projection after the live path has
  successfully accepted the input.
- Consume inputs on:
  - new wake start,
  - active attach publish,
  - deduped existing wake,
  - restart from pending trigger.
- Leave live `tq_pending_triggers` behavior unchanged.

## Out Of Scope

- Do not make the inbox projection live.
- Do not delete or stop writing `tq_pending_triggers`.
- Do not change attach handler behavior.
- Do not change watchdog/recovery semantics.
- Do not add an outbox worker.

## Small Tickets

- [x] **FSM-05B-A Ledger consumption API**: expose explicit methods to list
  unconsumed input events and mark input events consumed using caller-provided
  timestamps.
- [x] **FSM-05B-B Dispatch consumption accounting**: mark start/attach/dedupe
  inputs consumed only after the legacy side effect succeeds.
- [x] **FSM-05B-C Restart consumption accounting**: mark buffered inputs
  consumed when `session_ended()` successfully starts the restart wake.
- [x] **FSM-05B-D Tests**: prove attached inputs are consumed, buffered inputs
  remain unconsumed, and restart consumes pending inputs.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr240_input_consumption_observe.py`

## Explicit Dependency Boundary Review

Required shape:

- The ledger API must take `consumed_at` explicitly instead of reading time.
- `SessionRepository` may use its injected clock at the imperative boundary.
- Consumption decisions must derive from explicit live-path outcomes, not from
  a hidden scan of runtime globals.

## Legacy Cleanup Ledger

Keep these deliberately for now:

- `tq_pending_triggers` remains live pending state.
- `consumed_at` is an observe projection, not the authoritative scheduler state.

Deletion criteria:

- `tq_pending_triggers` can be removed only after a later cutover ticket derives
  pending/restart behavior from unconsumed input events and passes ordering
  tests.

## Verification

- `pytest tests/test_pr240_input_consumption_observe.py tests/test_pr239_append_only_inbox_observe.py tests/test_pr237_session_outbox_observe.py tests/test_pr153_pending_trigger_metadata.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. The new consumption account is observe-only and driven by explicit live
path outcomes: start, attach, dedupe, and restart. Buffered inputs remain
unconsumed until the existing restart path accepts them. The implementation
adds `input_consumed` events plus a `consumed_at` projection without making
that projection authoritative.

## Rollback

Revert this PR. Consumption accounting is observe-only and does not own live
routing.
