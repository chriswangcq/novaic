# Implement SQLite Active Stack Read Adapter

## Problem Definition

Runtime read cutover needs one explicit adapter around `OperationalSqliteStore.get_active_stack`. The adapter should provide response-compatible frames, stack depth/top access, and current active path resolution without leaking raw SQLite row handling into API endpoints.

## Proposed Solution

Extend the active stack projection module with read-side helpers:

- `read_active_stack_projection(operational_store, root_scope_id, root_scope_path)` or equivalent.
- Return normalized top-first frames, `stack_depth`, `top_scope_id`, and `active_scope_path`.
- For empty stack, return root path as active path.
- For non-empty stack, require top frame `scope_path` and fail loudly if missing.
- Keep helper pure over explicit store/root inputs.
- Add focused unit tests.

## Acceptance Criteria

- Adapter returns empty stack and root active path for missing/empty projections.
- Adapter returns top-first frames and top `scope_path` for non-empty projections.
- Adapter rejects non-empty projection frames missing `scope_path`.
- Adapter requires explicit operational store/root inputs.

## Verification Plan

- Extend `test_active_stack_projection.py`.
- Run helper/operational-store tests.
- Run `py_compile` on helper module.

## Risks

- If the adapter silently accepts old rows missing `scope_path`, P032/P033 could fall back into file-walk behavior. Fail loud instead.

## Assumptions

- Old persisted data may be discarded; no compatibility for incomplete active-stack rows is required.
