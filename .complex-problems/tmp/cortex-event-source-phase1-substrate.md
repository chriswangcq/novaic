# Phase 1: Context event store substrate

## Problem

Implement the Cortex context event source substrate: event types, event envelope, stream append/read APIs, idempotency, generation/versioning, and tests. This phase should not yet replace every caller, but it must establish the new source-of-truth substrate.

## Success Criteria

- Event schema/types are explicit and deterministic.
- Event append enforces stream identity, monotonic sequence/version, and idempotency key behavior.
- Event read supports replay by agent-root stream.
- Unit tests cover append, duplicate idempotency, ordering, invalid events, and reset/no-compat initialization.
- No hidden time/id dependencies in core event logic; clock/id providers are explicit where needed.
