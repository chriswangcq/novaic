# Ticket: Verify direct scope-end contract

## Goal

Audit and verify `/v1/scope/end` direct archive behavior for structured archive diagnostics, active stack finalize ownership, retry behavior, and test coverage.

## Acceptance Criteria

- `ScopeEndRequest` diagnostics validation is explicit and tested.
- `scope_end` writes wake archive events and active stack finalization through explicit helpers.
- Retry/idempotent behavior does not silently corrupt active stack state.
- Focused tests or guards pass.
- Any live contract gap is fixed or split.
