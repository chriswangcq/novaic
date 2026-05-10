# Emit SkillScopeClosed on skill_end success result

## Summary

Wired successful `/v1/context/skill_end` to append `SkillScopeClosed` with exact report text after LIFO validation and before transitional filesystem closure.

## Done

- Updated `context_skill_end` to append `SkillScopeClosed` only after:
  - requested child scope id is present;
  - active stack is not empty at root;
  - requested id equals the current stack top.
- Kept missing id, empty stack, and LIFO mismatch failure paths event-silent.
- Preserved legacy `complete_child_scope` so `summary.md` and scope meta remain transitional projections.
- Added focused tests for:
  - successful close event exact report text;
  - missing id no close event;
  - empty stack no close event;
  - scope mismatch no close event.

## Evidence

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- Focused tests: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_writer.py tests/test_context_event_projection.py -q` → `38 passed`
- Full suite: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `449 passed`

## Residual Risk

- Event append happens before legacy `complete_child_scope`; this makes the event stream authoritative if projection write fails, but is still transitional until cleanup.
- Lifecycle boundary audit is handled by P040.
