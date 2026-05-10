# Cut Skill Begin Parent Selection To SQLite

## Problem Definition

`skill_begin` still uses file-walk state to determine stack depth and parent path. After Phase 3B writes active-stack projection, new child scopes should attach under the SQLite top frame, or under the root when the projection is empty.

## Proposed Solution

- Use `read_active_stack_projection` in `skill_begin` for current stack frames and active parent path.
- Replace `resolve_active_scope_path(root_path)` for parent selection with the adapter's `active_scope_path`.
- Preserve existing duplicate/depth-limit/error response shapes.
- Keep `_collect_active_stack` only where failure response context still explicitly belongs to P020 or subsequent cleanup.
- Add tests that monkeypatch `resolve_active_scope_path` or `_collect_active_stack` as needed to prove parent selection uses SQLite projection.

## Acceptance Criteria

- Empty projection begins the first child under root.
- Non-empty projection begins the next child under the SQLite top frame path.
- Depth limit uses SQLite projection depth.
- Existing begin response shape remains compatible.
- Tests cover fresh Workspace/registry reading persisted SQLite projection for parent selection.

## Verification Plan

- Update skill lifecycle tests.
- Run targeted begin/status/active-stack tests.
- Run full Cortex tests.

## Risks

- Some error branches still collect file-walk stacks for response context until P020; avoid widening this ticket beyond successful parent selection/depth authority.

## Assumptions

- Active-stack projection rows contain `scope_path` for non-empty frames.
