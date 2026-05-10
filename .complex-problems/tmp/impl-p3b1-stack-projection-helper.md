# Phase 3B1 Active Stack Projection Helper

## Problem

The operational store has `set_active_stack`, but runtime code lacks a small explicit helper for frame schema, generation, top-first ordering, and stack event payloads.

## Success Criteria

- Add a helper module or functions with explicit inputs for root scope id/path, frames, generation, and reason.
- Frames are normalized top-first with stable keys needed by API responses and later active-path routing.
- Helper writes via `OperationalSqliteStore.set_active_stack` and, where needed, appends durable scope/control events with idempotency keys.
- Unit tests cover empty, nested, and malformed frame inputs.
