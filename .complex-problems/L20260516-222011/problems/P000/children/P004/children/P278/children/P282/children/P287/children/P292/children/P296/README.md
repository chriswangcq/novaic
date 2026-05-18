# Problem: Session after-transaction publish and outbox boundary audit

## Problem

Audit helper methods that publish attach or wake/recovery outbox effects after DB transactions. Confirm durable outbox rows remain the authority even when a synchronous publish path returns task IDs to callers.

## Success Criteria

- Map publish-after-transaction helper methods with file references.
- Confirm side effects are backed by durable outbox rows and idempotency keys.
- Flag any direct side effect that bypasses outbox durability.
