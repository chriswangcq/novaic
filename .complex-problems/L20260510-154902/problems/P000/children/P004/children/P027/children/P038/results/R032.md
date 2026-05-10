# Emit SkillScopeOpened on skill_begin success result

## Summary

Wired successful `/v1/context/skill_begin` to append `SkillScopeOpened` events after child scope creation while preserving duplicate failure no-op behavior.

## Done

- Updated `context_skill_begin` to append `SkillScopeOpened` with:
  - child scope id;
  - resolved parent scope id;
  - skill name;
  - display name/task.
- Kept existing duplicate/invalid/depth-limit checks before event append.
- Added focused tests for:
  - successful begin event payload;
  - duplicate begin failure not appending another open event.

## Evidence

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- Focused tests: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_writer.py tests/test_context_event_projection.py -q` → `36 passed`
- Full suite: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `447 passed`

## Residual Risk

- Event append still happens after transitional child scope creation, so this is not yet a single atomic transaction.
- Skill close event emission is handled by P039.
