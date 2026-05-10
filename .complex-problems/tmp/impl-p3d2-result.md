# Skill Begin Error And Projection Cleanup Result

## Summary

Completed P036/T033. `context_skill_begin` now uses one SQLite active-stack projection snapshot for validation failures, duplicate failures, depth-limit responses, successful child push projection writes, and exception responses. It no longer calls `_collect_active_stack(...)`.

## Done

- Moved `read_active_stack_projection(...)` to the top of `_context_skill_begin_locked(...)`.
- Replaced missing/invalid/duplicate response stack data with projection-derived frames.
- Kept depth-limit authority on projection-derived `current_stack`.
- Replaced post-create `_collect_active_stack(...)` with an explicitly constructed new child frame prepended to the prior projection frames.
- Replaced exception diagnostic fallback with projection-derived `current_stack`.
- Added monkeypatch tests for success, duplicate, validation failures, and depth-limit failures proving `_collect_active_stack(...)` is not called.
- Added a static read-source guard asserting the `skill_begin` section contains `read_active_stack_projection` and no `_collect_active_stack`.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_pr234_control_stack.py`
  - Passed: 30 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 457 tests.
- Static audit:
  - `skill_begin` section no longer contains `_collect_active_stack(...)`.
  - Remaining `_collect_active_stack(...)` call sites are outside P036: wake creation seeding and `skill_end` exception diagnostics.

## Residual Risk

- Duplicate-ID cross-check still walks the scope tree for ID uniqueness. That is not active-stack authority and was intentionally not changed in P036.
- Wake creation seeding and `skill_end` exception cleanup remain for sibling P020 child problems.

## Changed Files

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
