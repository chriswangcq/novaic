# Filter Focused Pytest Target Inventory to Real Test Files

## Problem

The P513 focused pytest inventory included `novaic-agent-runtime/tests/unit/task_queue/__init__.py` in the selected focused test file list. This is not a real test file and should not count as a focused pytest target.

## Success Criteria

- Regenerate the selected focused test list so it includes only executable `test_*.py` files.
- Update the inventory artifact and counts.
- Record evidence that no non-test file remains in the selected list.
