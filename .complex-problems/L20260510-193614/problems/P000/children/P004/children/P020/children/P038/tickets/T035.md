# Cut Active Write Routing To SQLite Projection

## Problem Definition

`scope_write_assistant` and `steps_write` still use `Workspace.resolve_active_scope_path(...)` to find the current active child scope before writing assistant messages or tool steps. This keeps filesystem active-path walking on live write-routing hot paths even after SQLite active-stack projection became runtime stack authority.

## Proposed Solution

Route live writes through the SQLite active-stack projection:

- In `scope_write_assistant`, replace `resolve_active_scope_path(root_scope_path)` with `read_active_stack_projection(...).active_scope_path`.
- In `steps_write`, replace `resolve_active_scope_path(root_scope_path)` with `read_active_stack_projection(...).active_scope_path`.
- Update tests to use public stack-authoritative lifecycle (`scope_create` root/wake plus `context_skill_begin`) rather than direct non-wake `scope_create` for nested active child setup.
- Add monkeypatch/reopened Workspace tests proving assistant and step writes do not need filesystem active-path walking.
- Add static guards for these endpoint sections.

## Acceptance Criteria

- `scope_write_assistant` contains no `resolve_active_scope_path(...)` call and writes to projection active path.
- `steps_write` contains no `resolve_active_scope_path(...)` call and writes to projection active path.
- Root-only/wake-only and nested child routing still write to the expected scope path.
- Tests prove routing works after Workspace/registry reconstruction from the same operational SQLite store.

## Verification Plan

- Run targeted steps/write-assistant routing tests and read-source guard tests.
- Run static audit for `resolve_active_scope_path(...)` in `api.py`.
- Run the full Cortex test suite.

## Risks

- Existing tests or legacy callers may create non-wake active children directly with `scope_create`; those paths should be updated or removed because runtime stack authority now comes from `skill_begin` projection writes.
- Step event payload scope IDs must remain consistent with the target active path.

## Assumptions

- Runtime live child skills are opened through `context_skill_begin`, not direct non-wake `scope_create`.
- No compatibility fallback to filesystem active-path walking is required.
