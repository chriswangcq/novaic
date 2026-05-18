# P042 Result

## What Changed

- Added explicit `LEGACY_DIRECT_REPLY_TOOL` and `LEGACY_UNKNOWN_REPLY_VARIANT` constants in `novaic-agent-runtime/tests/test_pr48_turn_finalizer.py`.
- Updated finalizer tests so old direct `im_reply` references are legacy-negative fixtures.
- Fixed shell reply test names/docstrings that previously used `im_reply` wording for current shell/agentctl behavior.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr48_turn_finalizer.py`
  - 20 passed
- `rg -n "im_reply" tests/test_pr48_turn_finalizer.py`
  - remaining hits are legacy constants and legacy-negative test names only.

## Remaining Gap

Runtime activity projection tests and guard/smoke assertions remain in sibling problems.
