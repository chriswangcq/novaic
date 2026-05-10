# Phase 2 Scope Transition Events To SQLite

## Problem

Scope transition history is currently written to local NDJSON. Move this to the SQLite operational store.

## Success Criteria

- `scope_state.transition` records lifecycle events through the SQLite store.
- Runtime no longer requires local `scope_state_log_path` as authority.
- Tests cover transition recording, idempotent self-loop behavior, and failure semantics.

