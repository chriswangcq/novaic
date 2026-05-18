# Build Unit Tool Output Test Subset Ticket

## Problem Definition

P519 needs a validated focused target list for unit task queue, shell/tool-output, retry/replay, saga worker boundary, multimodal/history injection, user content, and explicit dependency boundary tests.

## Proposed Solution

Select all P513 inventory paths under `tests/unit/task_queue/` plus `tests/test_queue_explicit_dependencies.py`. Save the target list, counts, validation files, and a coverage map.

## Acceptance Criteria

- The selected list contains only existing `test_*.py` files.
- It includes all selected `tests/unit/task_queue/*.py` files from P513.
- It includes `tests/test_queue_explicit_dependencies.py`.
- Counts and coverage map are recorded.

## Verification Plan

- Validate file existence and basename shape.
- Compare selected unit task queue count against P513 inventory matches.
- Save artifacts under `.complex-problems/L20260516-222011/tmp/p528/`.

## Risks

- Overlap with P518 could duplicate coverage, but duplication is acceptable if explicit and bounded.
- Omitting explicit dependency boundary would weaken P519.

## Assumptions

- P513 selected focused inventory remains authoritative.
