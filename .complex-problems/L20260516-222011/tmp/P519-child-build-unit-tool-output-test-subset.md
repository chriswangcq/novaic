# Build Unit Tool Output Test Subset

## Problem

Construct the P519 unit/tool-output/task_queue focused pytest target list from the P513 selected focused inventory.

## Success Criteria

- The generated list contains only existing `test_*.py` files.
- It includes `tests/unit/task_queue` tests and any selected explicit dependency/boundary tests assigned to P519.
- Filter terms, counts, and coverage mapping are recorded.
- Exclusions are justified rather than silent.
