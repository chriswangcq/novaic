# P045 Result

## What Changed

- Introduced `LEGACY_ARCHIVED_TOOL_LABELS` in `activity_projection.py`.
- Moved archived direct-tool display labels behind `_legacy_tool_name(...)` constants so raw migrated tool tokens are not scattered through generic label logic.
- Kept shell `desc` handling as the primary current-path monitor text.

## Verification

- `python3 -m py_compile task_queue/utils/activity_projection.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr193_activity_projection.py`
  - 8 passed
- Focused direct-tool scan over `activity_projection.py`
  - no direct-tool token matches.

## Remaining Gap

Frontend ActivityTimeline legacy detection remains in `P046`.
