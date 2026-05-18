# P528 Check: Build Unit Tool Output Test Subset

## Summary

Success. The P519 unit/tool-output/task_queue focused target list was built and validated as a 12-file subset.

## Evidence

- Result: `R519`
- Target list: `.complex-problems/L20260516-222011/tmp/p528/unit-tool-output-test-files.txt`
- Counts: `.complex-problems/L20260516-222011/tmp/p528/unit-tool-output-test-counts.txt`
  - `source_count=85`
  - `unit_task_queue_source_count=11`
  - `selected_count=12`
- Validation files:
  - `missing-paths.txt`: 0 lines
  - `non-test-basenames.txt`: 0 lines
- Coverage map: `.complex-problems/L20260516-222011/tmp/p528/coverage-map.md`

## Criteria Map

- Selected list contains only existing `test_*.py` files: satisfied.
- Includes all selected `tests/unit/task_queue/*.py` files from P513: satisfied by `unit_task_queue_source_count=11` and selected list.
- Includes `tests/test_queue_explicit_dependencies.py`: satisfied.
- Counts and coverage map recorded: satisfied.

## Execution Map

- Filtered P513 selected inventory for `tests/unit/task_queue/` plus `tests/test_queue_explicit_dependencies.py`.
- Validated existence and basename pattern.
- Wrote coverage map for P519 domains.

## Stress Test

- Empty-list risk: rejected by `selected_count=12`.
- Missing explicit dependency test risk: rejected by target list inclusion.
- Lost unit-task-queue test risk: reduced by matching all 11 unit task queue files from P513.

## Residual Risk

P528 only validates the target list. P529 must run pytest and P530 must audit coverage/result closure.

## Result IDs

- `R519`
