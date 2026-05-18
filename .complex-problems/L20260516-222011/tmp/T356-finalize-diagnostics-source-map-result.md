# T356 Result: Finalize Diagnostics Source Map

## Source Map

### Upstream finalize producers

- `task_queue/contracts/react_think.py`
  - Builds `wake_finalize` trigger payload with `finalize_reason`, `stack_depth_at_finalize`, `stack_known_at_finalize`, and `remaining_stack`.
  - Uses explicit positive session generation through `ReactThinkInput`.
- `task_queue/contracts/react_actions.py`
  - Builds `wake_finalize` trigger payload with forced or normal `finalize_reason` and `remaining_stack`.
  - Uses explicit positive session generation through `ReactActionsInput`.
- `queue_service/saga_repo.py`
  - Compensation path can create `wake_finalize`.
  - Now requires positive explicit `session_generation`.
  - Copies `remaining_stack`, `stack_known_at_finalize`, and `stack_depth_at_finalize` from saga context when present.

### Wake-finalize payloads

- `task_queue/sagas/wake_finalize.py`
  - `_build_cortex_scope_end_payload` forwards `scope_id`, `agent_root_scope_id`, `wake_scope_path`, `session_generation`, `finalize_reason`, and `round_num`.
  - `_build_session_ended_payload` forwards `scope_id`, `agent_root_scope_id`, `wake_scope_path`, `finalize_reason`, positive generation, `remaining_stack`, and `round_num`.
  - `_remaining_stack_snapshot` uses explicit `remaining_stack` when present, otherwise falls back to stack-known/depth fields.

### Session-ended queue boundary

- `task_queue/handlers/session_handlers.py`
  - Requires `finalize_reason`, positive `generation`, and object `remaining_stack`.
  - Forwards these to `saga_client.session_ended`.
- `task_queue/client.py` and `queue_service/routes.py`
  - Enforce positive generation at client/API boundary.
- `queue_service/session_repo.py`
  - Builds `finalize_metadata` from explicit `finalize_reason`, `finalize_generation`, `remaining_stack`, and `ended_scope_id`.
  - Calls `decide_session_finalize` before recording finalized or rejected events.
  - Records closed/restart transition metadata using the same `finalize_metadata`.
- `queue_service/session_ledger.py`
  - `record_session_finalize_rejected` stores `finalize_metadata` plus reject result, with idempotency key including scope/generation/reason.
  - `record_session_finalized` stores `finalize_metadata`, with idempotency key including scope/event generation/reason.

### Cortex archive boundary

- `task_queue/handlers/cortex_handlers.py`
  - Requires positive `session_generation` before calling Cortex archive.
  - Reads `finalize_reason` and logs/returns it.
  - Does not pass `session_generation`, `finalize_reason`, `remaining_stack`, or `ended_at` through `CortexBridge.scope_end`.
- `task_queue/utils/cortex_bridge.py`
  - `scope_end` currently sends only tenant, `scope_id`, `report`, `is_root`, and optional `scope_path`.
- `novaic-cortex/novaic_cortex/api.py`
  - `ScopeEndRequest` currently has `scope_id`, `report`, `scope_path`, and `is_root`.
  - `_append_wake_archived_event` writes a context event with generic reason (`scope_end_root` / `scope_end_child`) and remaining stack computed from current active-stack projection.
  - `_finalize_active_stack_for_archive` uses an active-stack generation derived from Cortex time, with idempotency key root/finalized/reason.
- `novaic-cortex/novaic_cortex/workspace.py`
  - `archive_root_scope_projection` and child completion write `ended_at` using Cortex workspace clock.

## Classification

- Queue session finalized/rejected records are guarded by explicit scope/generation and are good implementation targets for tests.
- Cortex scope archive is guarded by positive generation at task handler entry, but the archive request does not carry the diagnostics fields into Cortex. Cortex therefore records generic reason/remaining-stack metadata from current active-stack projection rather than the wake-finalize payload boundary.

## Implementation Targets

- P367 should verify or harden Queue session finalized/rejected records around stale finalize and valid reason/stack persistence.
- P368 should extend or harden the Cortex archive boundary so archive diagnostics can be tied to explicit runtime finalize payload identity instead of only generic Cortex archive reason/current active-stack state.
- P369 should run aggregate tests and residue checks across both boundaries.

## Gap

The primary gap is at the Cortex archive boundary: `ScopeEndRequest`/`CortexBridge.scope_end` do not carry finalize diagnostics (`finalize_reason`, `session_generation`, `remaining_stack`, `ended_at`) into Cortex archive/context-event records.
