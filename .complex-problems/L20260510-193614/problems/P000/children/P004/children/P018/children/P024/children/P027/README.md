# Phase 3B3A Active Stack Finalize Helper

## Problem

P024 needs a durable operational finalize event, but there is not yet a small helper that snapshots the remaining active stack, appends an idempotent SQLite event with an explicit reason/generation, and clears the active-stack projection deterministically. Without this helper, archive call sites will duplicate state-shaping logic.

## Success Criteria

- Add a focused helper for active-stack finalization using explicit operational store, root scope id, frames, generation, reason, and idempotency key.
- Helper writes a durable operational SQLite event containing `remaining_stack`, `top_scope_id`, and `reason`.
- Helper clears the active-stack projection deterministically after recording the event.
- Helper retry with the same idempotency key returns the same event without conflicting duplicate writes.
- Unit tests cover empty and non-empty remaining stack cases.
