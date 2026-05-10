# Cut Skill End LIFO Validation To SQLite

## Problem Definition

`skill_end` still validates stack-empty, top mismatch, and successful close path by resolving active scope from file-walk state. It must use SQLite active-stack projection as the LIFO authority.

## Proposed Solution

- Use `read_active_stack_projection` at the start of `skill_end`.
- Use SQLite `top_scope_id` for stack-empty/mismatch checks.
- Use SQLite `active_scope_path` as the child path to close.
- After successful close, update projection from the previous SQLite frames with the top frame removed.
- Preserve existing response fields for missing id, empty stack, mismatch, success, and exception cases.
- Add tests proving success and mismatch paths do not call `resolve_active_scope_path`.

## Acceptance Criteria

- Empty-stack detection comes from SQLite projection.
- Mismatch detection compares requested id with SQLite top scope id.
- Successful close uses SQLite top frame `scope_path`.
- Projection after close is the previous SQLite stack minus the closed top.
- Existing structured error fields remain compatible.

## Verification Plan

- Update skill lifecycle tests for success, mismatch, and empty stack.
- Run targeted lifecycle/status/active-stack tests.
- Run full Cortex tests.

## Risks

- Exception branches may still use file-walk stack collection for fallback diagnostics until P020.
- Malformed SQLite projection rows should fail loudly via the adapter.

## Assumptions

- SQLite projection is current because Phase 3B writes begin/end/finalize paths.
