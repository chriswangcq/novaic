# PR-292 — Session Finalize Ownership

Status: Closed

## Goal

Make finalize a first-class FSM event with explicit reason, generation, and
remaining stack, so one close does not accidentally collapse unrelated wake or
child-skill state.

## Scope

- Normalize finalize request shape.
- Require reason, generation, and remaining stack snapshot where applicable.
- Route finalize state clearing through FSM/reducer.
- Archive orphaned child skill state in a structured way.

## Dependencies

- PR-285 FSM decision contract.
- PR-288 observed event handler.

## Risks

- Current tools may send partial finalize payloads.
- Strictness can break old clients unless compatibility is explicit.

## Acceptance Criteria

- Finalize path records event with reason, generation, and remaining stack.
- FSM owns active clearing decision.
- Tests cover child skill open at finalize and generation mismatch.

## Verification

- Finalize ownership tests.
- Skill close regression tests.

## Closure Notes

- Finalize request handling now requires explicit `finalize_reason`,
  `generation`, and `remaining_stack`.
- Session finalize acceptance/rejection goes through the pure finalize FSM and
  records durable `session_finalized` / `session_finalize_rejected` events.
- Scope/generation mismatches reject finalize without clearing the current
  active state.
- Wake finalize payloads carry remaining stack snapshots, and structural
  Cortex scope-end keeps report empty so no synthetic summary is persisted.
- Verified by finalize ownership, turn finalizer, and summary-boundary tests,
  plus full runtime suite: `pytest` in `novaic-agent-runtime` -> 357 passed.
