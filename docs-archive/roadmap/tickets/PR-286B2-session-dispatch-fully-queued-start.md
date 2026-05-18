# PR-286B2 — Session Dispatch Fully Queued Start

Status: Closed

## Goal

Remove immediate wake creation from the normal dispatch start path and return a
queued wake contract consistently.

## Scope

- Dispatch start path appends outbox and returns before saga creation.
- Worker/observed event path activates the wake.
- Update tests and callers that currently expect immediate `saga_started`.

## Dependencies

- PR-286B1.
- PR-286B2A.
- PR-286C.
- PR-286D.

## Acceptance Criteria

- Normal dispatch no longer requires a synchronous saga id.
- Wake creation still reaches active via worker/reducer.
- Full suite passes under the new return contract.

## Verification

- Full dispatch/outbox/recovery tests.

## Closure Notes

- Closed through PR-286B2A, PR-286C1, PR-286D1, and PR-286D2.
- Normal dispatch start is now fully queued: input append, `starting` state,
  and create-wake outbox are committed before returning, without synchronous
  saga creation.
- A second dispatch during `starting` buffers against the retained planned
  scope rather than creating a duplicate wake.
- Wake activation is completed by draining the create-wake outbox and applying
  wake-created observation.
- Verified by targeted dispatch/outbox/restart tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
