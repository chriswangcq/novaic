# PR-287 — Outbox Publisher No State Mutation

Status: Closed

## Goal

Keep outbox publishers as side-effect adapters only. They may publish and
record publication observations, but they must not directly mutate session
state.

## Scope

- Move state transition after publish into observed-event handling.
- Remove state writes such as active-session recording from publisher methods.
- Ensure publisher output is an observation event that the FSM can reduce.

## Dependencies

- PR-286 durable wake creation cutover.
- PR-288 observed event handler.

## Risks

- Current dispatcher records active session after saga creation.
- Removing this too early can leave sessions permanently queued.

## Acceptance Criteria

- `SessionOutboxDispatcher` does not call state mutation methods such as
  `record_active_session`.
- Publisher records only outbox publication metadata or observed events.
- Reducer handles publication observation and owns state transition.

## Verification

- Grep review for state mutation calls in outbox dispatcher.
- Observed event reducer tests.

## Closure Notes

- Removed direct active-state mutation and input consumption from
  `SessionOutboxDispatcher._publish_create_wake_saga`.
- Added `SessionObservedEventHandler` as the owner of wake-created state
  application.
- Updated residue guards to require `record_active_session` outside
  `session_outbox.py`.
- Note: the publisher still calls the observed handler synchronously; routing
  every observed publication through a durable observed-event reducer remains
  PR-288B/PR-286C.
- Verified with targeted observed/outbox/residue tests: 15 passed.
