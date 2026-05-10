# Physically Remove Live Local Authority Residue

## Problem Definition

P045 found that the obvious old active-stack helpers are gone, but live Cortex still has local file/tree authority residue: `_walk_scope_tree` is used as a duplicate scope-id cross-check and described as filesystem ground truth, root meta `scope_ids` is a file-backed uniqueness index, and some compatibility wrappers may still exist. P046 must replace or quarantine these paths without breaking current scope lifecycle behavior.

## Proposed Solution

- Split the implementation into focused child problems:
  - Move scope-id uniqueness authority off root `meta.scope_ids` / `_walk_scope_tree` and into operational SQLite or an explicit projection.
  - Quarantine remaining `_walk_scope_tree` usage to archive/debug projection only, or remove it if no longer needed.
  - Review and delete/rename compatibility wrappers that no longer serve an active contract.
  - Run targeted scope lifecycle, active stack, operational store, and context event tests after each slice.

## Acceptance Criteria

- `skill_begin` does not rely on filesystem tree walking or root meta as authority for duplicate child scope id rejection.
- `_walk_scope_tree` is either removed from live API authority paths or documented/renamed as archive projection/debug-only.
- Old `scope_state_log.py` / local NDJSON transition log files remain deleted.
- Unneeded compatibility wrappers are removed, or explicitly justified as current API adapters.
- Tests assert the new authority paths and fail if old file-walk helpers return to runtime control logic.

## Verification Plan

- Run `rg` before and after for `_walk_scope_tree`, `scope_ids`, `resolve_active_scope_path`, `_collect_active_stack`, `scope_state_log`, and compatibility wrapper wording.
- Run targeted tests:
  - `test_context_event_api_skill_lifecycle.py`
  - `test_context_event_api_steps_write.py`
  - `test_active_stack_projection.py`
  - `test_operational_store.py`
  - `test_scope_state.py`
  - `test_scope_history_api.py`
  - `test_context_event_read_source_guards.py`
- Run compile checks for modified Cortex modules.

## Risks

- Scope-id uniqueness touches lifecycle correctness; replacing it in one big patch risks subtle duplicate-scope regressions.
- `_walk_scope_tree` is also used for archive projection, so deletion requires either an alternative archive projection source or a deliberate quarantine.
- Some wrappers with "compatibility" wording may be public adapters despite stale names.

## Assumptions

- No backward compatibility with old local scope-id authority is required.
- SQLite operational state can be expanded for scope-id uniqueness if needed.
