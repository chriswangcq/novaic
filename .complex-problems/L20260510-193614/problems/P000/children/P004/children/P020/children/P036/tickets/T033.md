# Cut Skill Begin Residual File-Walk Stack Reads

## Problem Definition

`context_skill_begin` uses SQLite active-stack projection for successful parent selection, but still calls `_collect_active_stack(...)` in validation/duplicate/exception branches and after successful child creation to seed the projection. Those residual reads keep file-walk stack authority available inside a core runtime control endpoint.

## Proposed Solution

Refactor `_context_skill_begin_locked(...)` so a single SQLite projection snapshot is the stack source for the whole request:

- Read `active_stack = read_active_stack_projection(...)` before validation branches that need stack data.
- Use `current_stack = active_stack["frames"]` for missing ID, invalid ID, duplicate ID, depth-limit, and exception response shapes.
- After `create_scope_projection(...)`, compute the new child frame from `child_scope_id`, `req.skill_name`, `req.task`, `parent_path`, and `child_path`.
- Write the new active-stack projection as `[new_child_frame, *current_stack]`, without calling `_collect_active_stack(...)`.
- Preserve global uniqueness checks and existing response fields.
- Add tests that monkeypatch `_collect_active_stack(...)` to fail across begin validation/duplicate/success paths.

## Acceptance Criteria

- `_context_skill_begin_locked(...)` contains no `_collect_active_stack(...)` calls.
- Successful `skill_begin` stack output is top-first and matches the SQLite projection.
- Missing ID, invalid ID, duplicate ID, and depth-limit responses return projection-derived stack data.
- Existing uniqueness and lifecycle event behavior are preserved.

## Verification Plan

- Run targeted skill lifecycle tests for begin success, duplicate, nested begin, depth limit, and static guards.
- Run a static section check over `skill_begin` to confirm `_collect_active_stack` is absent and `read_active_stack_projection` is present.
- Run the full Cortex test suite.

## Risks

- Building the child frame manually must preserve the normalized frame fields expected by active-stack projection tests.
- Duplicate checks still use scope-id index/tree walking for ID authority; this ticket only removes stack-shape file walking, not the duplicate-ID filesystem cross-check.

## Assumptions

- SQLite active-stack projection is populated for root/wake before `skill_begin` runs.
- No old file-walk stack fallback should be retained.
