# PR-286B2A — Session Starting Dispatch Buffers

Status: Closed

## Goal

Treat `starting`/`ending`/`recovering` session states as occupied harness states
inside `SessionRepository.dispatch`, so a second input cannot start another wake
while the first wake creation outbox is still pending.

## Scope

- Read full `tq_session_state`, not only active session rows, before dispatch
  decision.
- Route non-active occupied states through the pure FSM decision.
- Record buffered transition with the current occupied state and retained scope.
- Add regression coverage for two messages arriving before wake-created
  observation.

## Dependencies

- PR-283.
- PR-285.

## Acceptance Criteria

- A dispatch arriving while state is `starting` returns `buffered`.
- No second create-wake outbox row is appended for the same starting session.
- Full runtime suite passes.

## Verification

- Targeted dispatch repository test.
- Full runtime suite.

## Closure Notes

- `SessionRepository.dispatch` now reads full `tq_session_state`, not only an
  active-session projection, before deciding.
- Occupied non-active states such as `starting` are routed through the pure FSM
  and return `buffered` instead of creating a second wake.
- The buffered transition records the retained planned scope and a pending
  projection marker.
- Verified by targeted session/outbox tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
