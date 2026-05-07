# PR-286B — Session Dispatch Queued Start Contract

Status: Closed

## Goal

Persist wake creation intent as `starting` plus durable outbox before returning
from dispatch, without requiring immediate saga creation.

## Scope

- Dispatch start path records `starting` state and pending create-wake outbox.
- Return action names reflect queued wake creation.
- Existing synchronous compatibility is either removed or explicitly isolated.

## Dependencies

- PR-293 return contract.
- PR-286A worker substrate.

## Acceptance Criteria

- Dispatch does not require saga id to return success.
- Pending input remains durable while state is `starting`.
- Tests cover queued start and retry.

## Verification

- Dispatch contract tests.
- Inbox/outbox persistence tests.

## Closure Notes

- Closed through PR-286B1, PR-286B2, and PR-286B2A.
- Dispatch start now persists input, `starting` state, and create-wake outbox
  before returning `wake_start_queued`.
- A dispatch that arrives while the session is `starting` buffers and does not
  allocate a duplicate wake scope/outbox.
- Verified by targeted dispatch/state tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
