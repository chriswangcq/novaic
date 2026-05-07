# PR-288 — Session Observed Event Handler

Status: Closed

## Goal

Add a single handler that consumes observed events and applies the pure FSM
transition to the durable ledger.

## Scope

- Handle wake-created, attach-published, archive-published, publish-failed,
  finalize-requested, and watchdog-suspected-dead observations.
- Re-check active generation where relevant.
- Make event application idempotent.

## Dependencies

- PR-285 FSM decision contract.
- PR-287 publisher no-state-mutation.

## Risks

- Double publication or retry can replay the same observed event.
- Generation mismatch handling must be explicit.

## Acceptance Criteria

- State-changing effects after publication are routed through one observed
  event handler.
- Handler is idempotent and generation-checked.
- Tests cover duplicate observation and stale generation.

## Verification

- Targeted observed-event handler tests.
- Recovery and attach tests.

## Closure Notes

- Closed through PR-288A and PR-288B.
- Wake-created observation is the only side-effect observation that mutates
  active session state after publish; it is now handled by
  `SessionObservedEventHandler`.
- Active attach was re-classified as a durable handoff: transition, attach
  outbox, and input consumption are committed atomically, then the outbox owns
  delivery/retry.
- Archive/failure effects remain represented by durable outbox status because
  they do not change the session FSM state.
- Verified by observed-event, attach, recovery, finalize, outbox, and full
  runtime tests: `pytest` in `novaic-agent-runtime` -> 357 passed.
