# Wrapper Boundary Count Failure Ticket

## Problem Definition

`test_session_repository_no_longer_owns_outbox_append_publish_helpers` expects two `require_outbox=True` occurrences in `session_repo.py`, but current source has one.

## Proposed Solution

Inspect the test and current session repository source to determine whether the count expectation is stale after cleanup. Apply the minimal correct update and rerun the specific failing test.

## Acceptance Criteria

- Root cause is recorded with source/test references.
- Minimal correct code/test update is applied.
- The specific failing test passes.

## Verification Plan

- Run the single failing pytest test.
- Record changed files and command output.

## Risks

- Lowering a guard count could hide loss of a required outbox boundary if not paired with semantic assertions.

## Assumptions

- The test already has additional semantic assertions for required outbox behavior beyond the raw occurrence count.
