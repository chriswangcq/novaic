# Phase 2B Scope Transition Write Cutover To SQLite

## Problem

Scope lifecycle transitions currently append durable rows through `scope_state_log.append_transition` into an NDJSON file. Change the canonical write path so non-noop transitions append to operational SQLite `scope_events` through explicit workspace/store dependencies.

## Success Criteria

- `scope_state.transition` or its immediate caller appends transition events to `OperationalSqliteStore.scope_events`.
- Transition events include root scope identity, scope id/path, from/to state, reason, actor, metadata, and created timestamp.
- Existing non-noop/idempotent behavior is preserved: noop transitions do not append.
- Tests prove child and root archive transitions write one SQLite event each.
