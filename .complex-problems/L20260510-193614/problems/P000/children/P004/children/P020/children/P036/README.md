# Skill Begin Error And Projection Cleanup

## Problem

`context_skill_begin` still calls `_collect_active_stack(...)` in validation/duplicate/error responses and after successful child creation to seed the new active-stack projection. This means error surfaces and post-create writes can still reintroduce file-walk-derived stack authority.

This belongs under Phase 3D because `skill_begin` is a core runtime control path and its success path was only partially cut over in Phase 3C.

## Success Criteria

- Missing/invalid/duplicate/depth-limit `skill_begin` responses use SQLite projection-derived stack frames.
- Successful `skill_begin` computes the new stack by prepending the newly-created child frame to the projection frames already read for parent selection.
- `skill_begin` does not call `_collect_active_stack(...)` in success, validation, duplicate, or exception branches.
- Tests cover missing ID, invalid ID, duplicate ID, depth limit, and successful nested begin without file-walk stack collection.
