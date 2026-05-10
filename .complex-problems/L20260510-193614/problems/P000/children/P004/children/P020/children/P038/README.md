# Active Path Routing Endpoint Cutover

## Problem

Non-stack endpoints such as `scope_write_assistant` and `steps_write` still call `resolve_active_scope_path(...)` to route writes to the active child scope. Even if these calls are not LIFO decisions, they are live runtime routing decisions and can keep filesystem stack walking on hot paths.

This belongs under Phase 3D because active-path routing must have an explicit boundary: either use SQLite active-stack projection for live routing, or be documented as non-stack repair/debug behavior. The user does not want hidden compatibility branches.

## Success Criteria

- `scope_write_assistant` writes to `read_active_stack_projection(...).active_scope_path`, not `resolve_active_scope_path(...)`.
- `steps_write` writes tool steps to `read_active_stack_projection(...).active_scope_path`, not `resolve_active_scope_path(...)`.
- Returned `scope_path` and event `scope_id` behavior remain compatible for root-only and nested active skill sessions.
- Tests cover assistant write and step write targeting a nested active scope after reconstructing Workspace/registry state from operational SQLite.
