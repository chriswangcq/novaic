# Ticket: Remove or classify observed wake outbox residue

## Problem Definition

`OBSERVE_CREATE_WAKE_SAGA` appears as a stale session outbox effect name even though observed wake-created is now handled directly under `create_wake_saga` delivery. Determine whether production source still needs the constant and clean up residue.

## Proposed Solution

- Search source and tests for `OBSERVE_CREATE_WAKE_SAGA`.
- If production source constant is unused by live code, remove it.
- Preserve/update tests only as negative guards proving no observed-wake outbox effect is emitted or supported.
- Run focused tests covering observed wake outbox cleanup and wake creation outbox cutover.

## Acceptance Criteria

- Production source no longer exposes unused observed-wake effect residue unless explicitly justified.
- Tests still guard against reintroducing the obsolete observed-wake outbox effect.
- Focused tests pass.

## Verification Plan

- `rg OBSERVE_CREATE_WAKE_SAGA` before/after.
- Focused pytest for observed wake cleanup and wake creation outbox cutover.
