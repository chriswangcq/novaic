# Make FSM event replay a no-op for state and outbox

## Problem Definition

The generic FSM runner records event, state, and outbox in order. When the event insert is an idempotent duplicate, the store currently returns the existing event ID but the runner still upserts materialized state and attempts outbox writes. That can corrupt session state during message redelivery.

## Proposed Solution

Extend the generic SQLite store with a result that reports whether event append inserted a new row or reused an existing idempotent row. Keep the existing `append_event()` API returning `str`. Update `FsmTransitionRunner.record()` to return immediately on duplicate event replay before state/outbox writes.

## Acceptance Criteria

- Existing callers of `append_event()` still receive a string event ID.
- New runner path can detect duplicate event replay.
- Duplicate transition replay leaves materialized state unchanged.
- Duplicate transition replay emits no outbox effects.

## Verification Plan

- Add a regression test using session FSM store config and generic runner.
- Run the generic FSM runner tests.

## Risks

- Generic infrastructure change affects task, saga, session, and lease ledgers; compatibility of `append_event()` must be preserved.

## Assumptions

- Duplicate event idempotency key means the entire transition was already processed or is in progress and must not rematerialize fresh state.
