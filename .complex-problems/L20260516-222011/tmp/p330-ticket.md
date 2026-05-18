# Ticket: Audit repository-side attach payload generation

## Problem Definition

Inspect how `SessionRepository` creates attach requests, computes `expected_session_generation`, and records the attach outbox effect. Verify repository-side code does not silently convert a stale scope attach into a current-generation payload.

## Proposed Solution

Read the attach branch in `session_repo.py`, the active-session read helper, and `SessionLedgerRepository.active_generation(...)`. Search related tests for expected generation assertions. If a stale active scope can produce an attach payload for the wrong generation/scope, fix the repository or ledger helper and add a focused test.

## Acceptance Criteria

- Attach request creation and expected generation computation are mapped with file references.
- `active_generation(...)` scope mismatch behavior is classified.
- Repository-side stale-scope attach behavior is tested or fixed.
- Result identifies whether P331/P332 still need to verify downstream preservation/enforcement.

## Verification Plan

Run focused source searches and targeted tests for active inbox dispatch, attach outbox cutover, and session state SSOT. Add a test if the stale-scope repository behavior lacks coverage.

## Risks

- A downstream runtime rejection may mask repository-side bad outbox rows, leaving confusing dead-letter behavior.
- Current tests may only cover happy-path attach generation.

## Assumptions

- Repository should not knowingly enqueue attach for a stale active scope.
