# PR-291 — Session Watchdog Recovery FSM

Status: Closed

## Goal

Make watchdog and recovery transitions event-driven instead of direct state
mutation shortcuts.

## Scope

- Watchdog emits `SessionSuspectedDead` event.
- Recovery transition moves pending input to a recovery wake through FSM effects.
- Pending inbox remains durable across dead-wake replacement.
- Recovery does not bypass generation checks.

## Dependencies

- PR-288 observed event handler.
- PR-290 critical failure semantics.

## Risks

- Existing recovery tests may rely on direct state mutation.
- Misordered recovery can duplicate user input.

## Acceptance Criteria

- Watchdog does not directly clear active session state.
- Recovery wake creation is an outbox effect.
- Pending inbox migration is covered by tests.

## Verification

- Watchdog/recovery tests.
- Replay/rebuild tests.

## Closure Notes

- `wake_finalize` failure records `session_suspected_dead` instead of directly
  mutating active session state.
- The next dispatch observes the suspected-dead event, records a
  `session_suspected_dead_observed` transition, preserves pending inbox input,
  and queues a recovered wake through durable create-wake outbox.
- Recovery archive is also a durable outbox effect, retryable independently
  from wake creation.
- Wake activation still goes through generation/scope checked wake-created
  observation.
- Verified by recovery tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
