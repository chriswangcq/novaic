# Phase 2A Result

## Summary

Audited the current scope transition persistence path and defined the SQLite event mapping for Phase 2.

## Done

Writer call sites:

- `novaic-cortex/novaic_cortex/workspace.py:307-316`
  - `Workspace.complete_child_scope(...)` writes `summary.md`, then calls `scope_state.mark_archived(... transition_log_path=self._scope_state_log_path, created_at_ms=...)`.
- `novaic-cortex/novaic_cortex/workspace.py:413-422`
  - `Workspace.archive_root_scope(...)` writes root `summary.md`, then calls `scope_state.mark_archived(... transition_log_path=self._scope_state_log_path, created_at_ms=...)`.
- `novaic-cortex/novaic_cortex/scope_state.py:161-249`
  - `transition(...)` updates `meta.phase`, emits logs, then calls `scope_state_log.append_transition(...)` when `transition_log_path` is present.
- `novaic-cortex/novaic_cortex/scope_state.py:255-272`
  - `mark_archived(...)` is the convenience wrapper used by workspace lifecycle paths.

Reader call sites:

- `novaic-cortex/novaic_cortex/api.py:642-653`
  - `/v1/scope/history` uses `_registry.scope_state_log_path` and `scope_state_log.list_transitions(...)`.
- `novaic-cortex/tests/test_scope_state_log.py`
  - Tests raw `append_transition`, `list_transitions`, and direct transition integration.
- `novaic-cortex/tests/test_scope_state.py`
  - Patches `scope_state_log.append_transition` and asserts non-noop transition logging.

Current NDJSON row shape:

- `ts_ms`
- `scope_path`
- `from_state`
- `to_state`
- `reason`
- `actor`
- optional `metadata`

Target SQLite event mapping:

- `scope_events.root_scope_id`: root scope id parsed from the logical `scope_path`.
- `scope_events.scope_id`: scope id parsed from the logical `scope_path`.
- `scope_events.event_type`: `scope_state_transition`.
- `scope_events.generation`: operational generation for this event stream; use `created_at_ms` as initial generation only if no better generation exists in Phase 2.
- `scope_events.reason`: transition reason such as `scope_end_root` or `scope_end_child`.
- `scope_events.payload`: preserve the current public row shape with `ts_ms`, `scope_path`, `from_state`, `to_state`, `reason`, `actor`, and optional `metadata`.
- `scope_events.occurred_at_ms`: current `created_at_ms`.
- `scope_events.idempotency_key`: deterministic transition key derived from root/scope path/from/to/reason/actor/created timestamp or omitted for existing non-idempotent write behavior. Phase 2B should prefer deterministic key when safe.

Cleanup stance:

- The NDJSON module/path should not remain authoritative after Phase 2.
- If old tests still need a reader shape, build it from SQLite rows rather than the flat file.
- `scope_state_log_path` should be removed from required startup/registry/workspace construction in Phase 2C if SQLite covers `/v1/scope/history`.

## Verification

- Ran `rg` over `novaic-cortex/novaic_cortex` and `novaic-cortex/tests` for `append_transition`, `list_transitions`, `transition_log_path`, `scope_state_log_path`, and `scope_history`.
- Read the relevant slices of `scope_state.py`, `scope_state_log.py`, `workspace.py`, `api.py`, `tests/test_scope_state.py`, and `tests/test_scope_state_log.py`.

## Known Gaps

- No code changed in this audit child. Phase 2B owns SQLite writer cutover; Phase 2C owns read cutover and NDJSON cleanup.

## Artifacts

- Audit evidence commands listed above.
