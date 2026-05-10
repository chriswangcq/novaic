# Phase 2C1 Scope History API Reads From SQLite

## Problem

The `/v1/scope/history` endpoint still reads from the NDJSON transition log through `_registry.scope_state_log_path`. It must read from operational SQLite instead.

## Success Criteria

- `/v1/scope/history` calls `list_scope_transition_events(_registry.operational_store, ...)`.
- Response no longer includes `log_path`; it should indicate SQLite/operational backend if any backend field remains.
- Tests cover scope history rows coming from SQLite.
