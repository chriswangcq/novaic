# Wire Skill Begin End Active Stack Writes

## Problem Definition

`skill_begin` and `skill_end` still only materialize workspace files and return file-walk stacks. SQLite active-stack projection exists, but successful begin/end operations do not write it, so later read cutover would see stale or empty stack state.

## Proposed Solution

Wire write-only projection updates:

- Enhance the current stack frame shape to include `scope_path`, `parent_scope_id`, `parent_path`, and `kind` so the SQLite projection can support later routing.
- On successful `skill_begin`, write the pushed top-first stack to operational SQLite using `write_active_stack_projection`.
- On successful `skill_end`, write the popped top-first stack to operational SQLite using `write_active_stack_projection`.
- Keep existing API responses file-walk-derived in this phase; runtime read cutover happens in P019.
- Add focused tests that inspect `workspace.operational_store.get_active_stack` after nested begin/end and after store reuse.

## Acceptance Criteria

- Successful `skill_begin` writes a SQLite active stack with the new child as `top_scope_id`.
- Successful `skill_end` writes a SQLite active stack with the closed child removed.
- Error branches do not mutate SQLite active-stack projection.
- Frame data includes enough path information for P019 active-path routing.
- Existing API response semantics remain compatible until read cutover.

## Verification Plan

- Add/update API lifecycle tests for active-stack projection writes.
- Run active-stack helper tests and affected skill lifecycle tests.
- Run `py_compile` on modified modules.

## Risks

- This phase still relies on file-walk stack as the source for API responses and shadow projection seed; P019 must remove that runtime read authority.
- Existing tests with mocked workspaces may need explicit operational-store wiring.

## Assumptions

- `Workspace.operational_store` is available for registry-built runtime workspaces.
- P023 does not solve finalize/root archive projection writes; that is P024.
