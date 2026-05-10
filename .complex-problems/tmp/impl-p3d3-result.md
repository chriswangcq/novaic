# Skill End Exception Diagnostic Cleanup Result

## Summary

Completed P037/T034. `context_skill_end` exception diagnostics now reuse the projection-derived stack captured at function entry and no longer call `_collect_active_stack(...)`.

## Done

- Removed `_collect_active_stack(...)` fallback from the `skill_end` exception branch.
- Kept structured exception response fields: `error_code`, `requested_scope_id`, `actual_stack_top`, `stack`, and `stack_depth`.
- Added a monkeypatch test that injects a close failure and makes `_collect_active_stack(...)` raise if called.
- Added a static read-source guard asserting the `skill_end` section contains `read_active_stack_projection` and no `_collect_active_stack`.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_pr234_control_stack.py`
  - Passed: 20 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 459 tests.
- Static audit:
  - `skill_end` section no longer contains `_collect_active_stack(...)`.
  - Remaining `_collect_active_stack(...)` call sites are wake creation projection seeding plus helper definition.

## Residual Risk

- The exception branch writes `SkillScopeClosed` before the injected close failure because that is the pre-existing operation order; this ticket only removes file-walk diagnostics and does not redesign transactional ordering.
- Wake creation seeding and active-path routing remain for sibling P020 child problems.

## Changed Files

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
