# PR-295 — Session Replay Audit Tooling

Status: Closed

## Goal

Provide a repeatable way to inspect/replay session events and explain why the
FSM reached a state, without relying on ad hoc debugging or LLM memory.

## Scope

- Add a small audit/replay utility or test helper for session events.
- Show input events, decisions, outbox effects, observed events, and final
  state.
- Keep it read-only unless explicitly invoked in tests.

## Dependencies

- PR-284 event vocabulary.
- PR-285 decision contract.

## Risks

- Tooling can become stale if it duplicates FSM rules.
- It should consume the same reducer, not reimplement logic.

## Acceptance Criteria

- Audit helper can replay a representative session event stream.
- Tests verify replay output for at least one start, attach, and finalize path.
- Documentation explains how to use it during incidents.

## Verification

- Replay helper tests.
- Manual read of docs snippet.

## Closure Notes

- Added `queue_service/session_audit.py` with read-only audit timeline and
  summary helpers.
- The helper consumes recorded decision traces instead of reimplementing FSM
  rules.
- Added `tests/test_pr295_session_audit_tooling.py`.
- Verified with targeted audit/FSM tests: 3 passed.
