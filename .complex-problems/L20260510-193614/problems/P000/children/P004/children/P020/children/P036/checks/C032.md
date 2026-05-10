# Skill Begin Error And Projection Cleanup Success Check

## Summary

P036 is solved. R030 removes file-walk active-stack collection from `context_skill_begin` across success, validation failure, duplicate failure, depth-limit, and exception response branches.

## Evidence

- `_context_skill_begin_locked(...)` now reads `read_active_stack_projection(...)` once and reuses `current_stack`.
- Successful begin writes `[new_child_frame, *current_stack]` to active-stack projection without scanning filesystem stack.
- Missing/invalid/duplicate/depth-limit responses return projection-derived stack frames.
- Exception responses return projection-derived stack frames instead of falling back to `_collect_active_stack(...)`.
- Targeted tests passed: 30 tests.
- Full Cortex suite passed: 457 tests.

## Criteria Map

- Missing/invalid/duplicate/depth-limit `skill_begin` responses use SQLite projection-derived stack frames: satisfied.
- Successful `skill_begin` computes new stack by prepending the new child frame to projection frames already read for parent selection: satisfied.
- `skill_begin` does not call `_collect_active_stack(...)` in success, validation, duplicate, or exception branches: satisfied by static guard and monkeypatch tests.
- Tests cover missing ID, invalid ID, duplicate ID, depth limit, and successful nested begin without file-walk stack collection: satisfied.

## Execution Map

- T033 was classified `one_go`.
- R030 records implementation and verification.
- No follow-up is required for P036.

## Stress Test

- Monkeypatch tests make `_collect_active_stack(...)` raise during begin success/failure branches.
- Static source guard checks the whole `skill_begin` section.
- Full suite ensures lifecycle behavior remains compatible after manually constructing projection frames.

## Residual Risk

- Duplicate-ID filesystem tree walking remains as ID uniqueness cross-check, not stack authority.
- Remaining `_collect_active_stack(...)` call sites are owned by sibling P020 children: wake creation seeding and `skill_end` exception diagnostics.

## Result IDs

- R030
