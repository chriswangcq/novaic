# PR-283 — Session State Taxonomy

Status: Closed

## Goal

Make the Queue session harness state taxonomy explicit enough that the queue
cannot confuse "no active wake" with "wake creation is in progress" or "current
wake cannot safely accept more input".

## Scope

- Add an explicit starting/in-flight wake creation state.
- Define which states may attach input and which states must buffer input.
- Keep status naming separate from delivery result naming.
- Add tests for dispatch decisions in each non-terminal state.

## Dependencies

- Existing generic FSM substrate.
- Existing `SessionRuntimeStatus` and `decide_session_dispatch`.

## Risks

- Existing tests assume immediate wake creation after `dispatch`.
- Recovery paths may currently rely on non-active states falling through to
  direct wake start.

## Acceptance Criteria

- State enum covers `no_active`, `starting`, `active`, `ending`,
  `suspected_dead`, and `recovering`.
- Pure dispatch decision does not start a new wake from non-attachable active
  lifecycle states.
- Unknown persisted `tq_session_state.state` values hard-fail instead of
  silently degrading to `no_active`.
- Active code writes state values through `SessionRuntimeStatus`, not scattered
  string literals.
- Tests document expected decisions for every state.

## Verification

- Targeted PR-283 FSM tests.
- Existing session FSM tests.

## Closure Notes

- Added explicit `SessionRuntimeStatus.STARTING`.
- Changed the pure dispatch reducer so only `no_active` starts a wake and
  lifecycle states (`starting`, `ending`, `suspected_dead`, `recovering`) buffer
  new input instead of accidentally starting another wake.
- Tightened persisted-state decoding: unknown states now raise, and repo/ledger
  state writes use the shared enum value.
- Added `tests/test_pr283_session_state_taxonomy.py`.
- Verified with targeted FSM tests: 17 passed after the hard-fail tightening.
