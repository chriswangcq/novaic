# Cortex projection missing regression implementation

## Problem

If the inventory finds missing Cortex projection coverage, add the smallest focused test changes to close the gaps.

## Success Criteria

- Missing regression tests are added or adjusted if needed.
- Tests assert no raw media/base64 is present in history/current non-display projection.
- Tests preserve explicit display perception as the only allowed media projection mode.
- No unrelated refactor or compatibility branch is introduced.
