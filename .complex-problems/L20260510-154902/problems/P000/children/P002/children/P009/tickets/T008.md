# Implement ContextEvent idempotency and reset semantics

## Problem Definition

The ContextEvent store can append events, but retry-safe idempotency is not yet enforced. Without this, retries can create duplicate context facts or silently accept conflicting facts under the same idempotency key. P009 must close that source-of-truth risk before later write-path cutover.

## Proposed Solution

- Extend `ContextEventStore.append_event` so that when `idempotency_key` is provided:
  - existing event with the same key and same canonical semantic body returns the existing event without appending;
  - existing event with the same key and different canonical semantic body raises a clear conflict error;
  - duplicate detection does not consume new id/clock provider values.
- Add a typed idempotency conflict error.
- Keep append without idempotency key possible for explicit non-idempotent events.
- Confirm `initialize_root` is retry-safe because it uses a stable root-init idempotency key.
- Add tests for duplicate reuse, conflict, provider non-consumption on duplicate, non-idempotent append, and repeated root initialization.

## Acceptance Criteria

- Same idempotency key + same semantic body does not append a duplicate.
- Same idempotency key + different semantic body fails loudly.
- Duplicate idempotent append returns the originally persisted event.
- Non-idempotent append still creates new events when explicitly requested.
- Root initialization is retry-safe and does not create duplicate `RootInitialized` events.
- Focused tests pass.

## Verification Plan

- Run event model/store tests.
- Static scan event store for hidden time/id/env reads and legacy DFS source fallback.
- Diff review to ensure idempotency is implemented in store only and no endpoint cutover is introduced.

## Risks

- If canonical body comparison omits too much, conflicts may be missed.
- If duplicate handling consumes providers, retries can become nondeterministic or exhaust injected test providers.

## Assumptions

- Canonical semantic body excludes generated fields but includes stream/root, actor, type, and payload.
- Store read path validates existing rows before idempotency comparison.
