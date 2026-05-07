# PR-286C1 — Wake Created Generation Guard

Status: Closed

## Goal

Make the wake-created observation reducer accept only observations that match
the current starting generation and planned scope, while remaining idempotent
for already-active duplicate observations.

## Scope

- Validate `generation` and `scope_id` against `tq_session_state` before
  activating.
- Stale or mismatched observations must not overwrite current state.
- Duplicate observations for the already-active same saga/scope remain harmless.

## Dependencies

- PR-288A.

## Acceptance Criteria

- Matching starting observation activates the session.
- Stale generation or wrong scope is ignored/cancelled and does not consume
  input.
- Duplicate active observation is idempotent.

## Verification

- Observed event reducer tests.

## Closure Notes

- `SessionObservedEventHandler.apply_wake_created` now requires generation and
  accepts only the matching `starting` state for the planned scope.
- Stale generation/wrong-scope observations cancel the loser saga if still
  pending and do not overwrite current state or consume inputs.
- Duplicate observations for an already-active winning saga/scope remain
  idempotent.
- Verified by `tests/test_pr288_session_observed_event_handler.py` and full
  runtime suite: `pytest` in `novaic-agent-runtime` -> 357 passed.
