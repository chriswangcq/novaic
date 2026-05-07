# PR-286C — Wake Created Observation Reducer

Status: Closed

## Goal

Apply a wake-created observation through the session FSM/ledger, not inside the
publisher.

## Scope

- Add observed event shape for wake creation success/failure.
- Reducer transitions `starting` to `active` on matching generation.
- Reducer consumes input event ids after activation.
- Duplicate and stale observations are idempotent.

## Dependencies

- PR-288 observed event handler.
- PR-287 publisher no-state-mutation.

## Acceptance Criteria

- Wake-created observation can activate a session from `starting`.
- Stale generation does not overwrite current active session.
- Input consumption is tied to activation observation.

## Verification

- Observation reducer tests.

## Closure Notes

- Closed through PR-288A and PR-286C1.
- Wake-created state activation and input consumption now live in
  `SessionObservedEventHandler.apply_wake_created`, not directly in the outbox
  publisher body.
- The handler accepts only matching generation/scope for the planned
  `starting` state and keeps duplicate active observations idempotent.
- Verified by observed event handler tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
