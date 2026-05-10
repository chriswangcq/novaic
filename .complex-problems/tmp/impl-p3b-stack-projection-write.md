# Phase 3B SQLite Active Stack Write Projection

## Problem

`skill_begin`, `skill_end`, and finalize need to update operational SQLite active-stack projection transactionally with their lifecycle events. Without this write path, runtime reads cannot safely cut over from file walking.

## Success Criteria

- A small adapter/helper writes active-stack frames to `OperationalSqliteStore.set_active_stack` with explicit root id, top scope id, generation, and frame schema.
- `skill_begin` updates SQLite active-stack projection after a successful child scope open.
- `skill_end` updates SQLite active-stack projection after a successful close.
- Finalize records explicit reason and remaining stack in a durable event/projection update.
- Tests cover nested begin/end and projection state after restart-like store reuse.
