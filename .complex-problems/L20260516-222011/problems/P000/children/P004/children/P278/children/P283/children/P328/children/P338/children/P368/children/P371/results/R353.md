# Cortex Archive Diagnostics Source Map Result

## Summary

Mapped the active `CORTEX_SCOPE_END` path from wake-finalize payload construction through runtime handler, bridge, Cortex API, active-stack finalization, and context-event archive writing. The gap is real: runtime validates `session_generation` and logs `finalize_reason`, but the bridge and Cortex API drop finalize diagnostics before archive persistence.

## Done

- Inspected `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`.
- Inspected `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`.
- Inspected `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`.
- Inspected `novaic-cortex/novaic_cortex/api.py`.
- Inspected `novaic-cortex/novaic_cortex/context_event_writer.py`.
- Inspected existing runtime and Cortex tests related to `scope_end`, `WakeArchived`, `ACTIVE_STACK_FINALIZED`, and generation validation.

## Verification

- Source search covered `CORTEX_SCOPE_END`, `scope_end`, `ScopeEndRequest`, `_append_wake_archived_event`, `_finalize_active_stack_for_archive`, `archive_root_scope_projection`, `finalize_reason`, `session_generation`, and `remaining_stack`.
- Runtime tests found: `tests/test_scope_end_environment_notifications.py`, `tests/test_pr70_explicit_skill_summary_only.py`, `tests/test_pr186_runtime_main_path_acceptance.py`, and finalize payload tests in `tests/test_pr254_finalize_ownership.py`.
- Cortex tests found: `tests/test_context_event_api_lifecycle.py`, `tests/test_context_event_api_skill_lifecycle.py`, `tests/test_context_event_write_authority.py`, and `tests/test_active_stack_projection.py`.

## Current Field Handling

- `wake_finalize._build_cortex_scope_end_payload` preserves `scope_id`, `agent_root_scope_id`, `wake_scope_path`, `agent_id`, `user_id`, positive `session_generation`, empty structural `report`, `finalize_reason`, and `round_num`.
- `handle_cortex_scope_end` requires positive `session_generation` using `require_positive_session_generation`; it logs and returns `finalize_reason`, `session_generation`, and `round_num`.
- `handle_cortex_scope_end` does not forward `session_generation`, `finalize_reason`, `round_num`, or `remaining_stack` to `bridge.scope_end`.
- `CortexBridge.scope_end` accepts only `scope_id`, `report`, `is_root`, and `scope_path`; it posts no archive diagnostics to `/v1/scope/end`.
- `ScopeEndRequest` accepts only tenant fields, `scope_id`, `report`, `scope_path`, and `is_root`; Cortex therefore cannot receive runtime finalize diagnostics.
- `_append_wake_archived_event` writes `WakeArchived` with `reason` and `remaining_stack` supplied by `scope_end`, currently generic `scope_end_root` or `scope_end_child`.
- `_finalize_active_stack_for_archive` records operational active-stack finalization with generation from `_active_stack_generation_ms(ws)`, not runtime `session_generation`.
- `scope_end` computes `remaining_stack` from active-stack projection using `_semantic_remaining_stack_after_archive`, not from runtime finalize payload.

## Implementation Targets

- P372 should update runtime handler/bridge/API request contract so archive diagnostics can cross the task/Cortex boundary.
- P373 should update Cortex archive/event persistence so explicit finalize diagnostics are recorded and invalid generation is rejected where diagnostics are supplied.
- P374 should run aggregate compile/tests/residue checks across runtime and Cortex.

## Known Gaps

- No code changes in this source-map ticket.
- Boundary propagation and persistence fixes remain open in P372 and P373.

## Artifacts

- Ticket: `.complex-problems/L20260516-222011/tmp/P371-cortex-archive-diagnostics-source-map-ticket.md`
