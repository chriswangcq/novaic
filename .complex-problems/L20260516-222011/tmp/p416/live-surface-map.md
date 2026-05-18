# P416 Cortex live-surface map

## Guard Summary

- `cortex-default-fallback-guard.txt`: header only; no fallback/default hits from the targeted regex.
- `cortex-generation-active-guard.txt`: 271 lines.
- `cortex-archive-event-guard.txt`: 1173 lines.

## Live Code Buckets

### Context Event Lifecycle

- `novaic-cortex/novaic_cortex/context_event_store.py`
- `novaic-cortex/novaic_cortex/context_event_writer.py`
- `novaic-cortex/novaic_cortex/context_events.py`
- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/novaic_cortex/context_event_read_model.py`
- `novaic-cortex/novaic_cortex/workspace.py`

Downstream owner: P417.

### Archive / Diagnostic / Projection

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/active_stack_projection.py`
- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/novaic_cortex/scope_state.py`
- `novaic-cortex/novaic_cortex/scope_transition_events.py`
- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/novaic_cortex/blob_payload.py`
- `novaic-cortex/novaic_cortex/context_stack/budget.py`
- `novaic-cortex/novaic_cortex/context_stack/types.py`

Downstream owner: P418.

### API / CLI / Runtime Bridge

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/logical_fs.py`
- `novaic-cortex/novaic_cortex/shell_capabilities.py`
- `novaic-cortex/novaic_cortex/main_cortex.py`
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`

Downstream owner: P419.

## Test Buckets

The following tests contain intentional generation/archive/context terms and should be used for verification rather than cleanup by regex:

- `novaic-cortex/tests/test_active_stack_projection.py`
- `novaic-cortex/tests/test_context_event_api_lifecycle.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_projection.py`
- `novaic-cortex/tests/test_context_event_read_model.py`
- `novaic-cortex/tests/test_context_event_store.py`
- `novaic-cortex/tests/test_context_event_writer.py`
- `novaic-cortex/tests/test_operational_store.py`
- `novaic-cortex/tests/test_pr74_scope_summary_contract.py`
- plus the remaining test files listed in `test-files.txt`.

## Non-Live / Guard Infrastructure

- `novaic-cortex/README.md`
- `novaic-cortex/scripts/check_cortex_boundary.py`

## Risk Candidates For Cleanup Children

1. `novaic-cortex/novaic_cortex/api.py`
   - `ScopeEndRequest` currently permits calls with no archive diagnostics at all. Runtime `cortex_handlers.py` passes explicit positive `session_generation` and `remaining_stack`, but direct API callers may still exercise a weaker path. P419 should decide whether to require diagnostics for all live `/v1/scope/end` calls or explicitly split projection-only/internal compatibility.

2. `novaic-cortex/novaic_cortex/active_stack_projection.py`
   - `read_active_stack_projection()` validates `row.get("generation", 0)`. Because `OperationalSqliteStore.get_active_stack()` returns generation 0 for absent rows, this may be a deliberate empty-projection sentinel or a hidden active-state fallback. P418 should classify or tighten it.

3. `novaic-cortex/novaic_cortex/operational_store.py`
   - `get_active_stack()` returns an empty stack with generation 0 when no active stack row exists. This is probably an operational projection sentinel, but it must be classified as non-session authority or changed to fail closed.

4. `novaic-cortex/novaic_cortex/workspace.py`
   - Archive projection helpers still walk workspace files for archive/debug projection only. Comments say runtime active-stack decisions must use SQLite projections. P418 should verify no live decision path depends on file walking.

5. `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
   - `read_session_meta` soft-fails before archive. This is intentionally trace-only, but P419 should confirm it cannot suppress required generation/finalize validation.

## Exclusions Applied

The guards excluded `.venv`, `__pycache__`, `.pytest_cache`, `node_modules`, `.git`, `.complex-problems`, `dist`, and `build`.
