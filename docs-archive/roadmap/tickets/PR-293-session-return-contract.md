# PR-293 — Session Return Contract

Status: Closed

## Goal

Align caller-visible dispatch/finalize return values with the durable FSM and
outbox reality.

## Scope

- Define return actions for queued wake creation, attached input, buffered
  input, pending recovery, duplicate/deduped input, and failed persistence.
- Update `common/wake/assembler.py` docs/contracts if needed.
- Make any caller compatibility explicit, temporary, and removed once the
  durable outbox return contract is the only active path.

## Dependencies

- PR-286 wake creation durable outbox cutover.

## Risks

- API consumers may expect `saga_id` immediately.
- Renaming actions without compatibility can break UI or business callers.

## Acceptance Criteria

- Return contract documents which actions have `saga_id` immediately and which
  are pending.
- Tests cover current delivery names and fail if old compatibility branches
  return.
- No caller relies on undocumented action names.

## Verification

- Contract tests.
- Route/assembler tests.

## Closure Notes

- Added `common/wake/dispatch_contract.py` with shared dispatch/finalize
  action names and classification helpers.
- Updated `DispatchResult` documentation and helpers so pending wake actions are
  not treated as immediate live wake handles.
- Added `pending_wake` and `has_immediate_scope` helpers to `DispatchResult`.
- Added `tests/test_pr293_session_return_contract.py`.
- Verified with targeted contract/scheduler tests: 6 passed.
