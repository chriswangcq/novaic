# Remove legacy runtime skill lifecycle bypass result

## Summary

Physically removed the legacy runtime skill lifecycle bypass. The only remaining skill lifecycle write path is the event-wired `/v1/context/skill_begin` and `/v1/context/skill_end` path.

## Done

- Deleted old JWT `/v1/skill/begin` and `/v1/skill/end` API routes and request models.
- Deleted `Cortex.skill_begin/end`.
- Deleted runtime in-memory `_active_skills` / `_skill_stack` state and accessors.
- Deleted `SkillInstance` type/export.
- Replaced old `tests/test_skill_lifecycle.py` with `tests/test_legacy_skill_lifecycle_removed.py`.
- Added guard assertions that old routes and runtime methods no longer exist.

## Evidence

- Static scan for old route/model/method/state names has no runtime hits; only guard tests and unrelated `skill_stack_snapshot` metadata remain.
- Focused tests: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_legacy_skill_lifecycle_removed.py tests/test_context_event_api_skill_lifecycle.py tests/test_runtime.py -q` → `8 passed`.
- Full suite: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `444 passed`.

## Residual Risk

- External callers of removed JWT skill routes will fail. That is intentional for this full cutover.
