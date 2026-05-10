# Phase 2C Scope History Read Cutover And NDJSON Cleanup

## Problem

The `/v1/scope/history` read path and scope transition tests still assume the NDJSON transition log is the machine-readable authority. Move history reads to SQLite and remove or explicitly demote old NDJSON wiring.

## Success Criteria

- `/v1/scope/history` reads transition history from operational SQLite.
- `scope_state_log_path` is removed from required Cortex startup/registry/workspace construction if no longer needed.
- Tests no longer require a transition NDJSON path for authoritative lifecycle history.
- Static searches show any remaining `scope_state_log`/NDJSON code is deleted or clearly projection/debug-only.
