# Unit Tool Output and Task Queue Focused Tests Ticket

## Problem Definition

P511 still needs focused coverage for unit-level task queue tests and tool-output/shell/retry/replay/user-content boundaries. These were deliberately excluded from P518 and must be verified separately.

## Proposed Solution

Build a P519 target list from the P513 selected focused inventory, covering `tests/unit/task_queue` and focused boundary tests such as queue explicit dependencies. Run pytest on that list, preserve exact evidence, and audit whether it closes P519.

## Acceptance Criteria

- The P519 selected subset contains only real `test_*.py` files.
- The subset covers unit task queue, shell/tool-output, retry/replay, saga worker boundary, multimodal/history injection, and explicit dependency boundary tests.
- Pytest exits successfully for the validated subset.
- Exact target count, command, collected test count, and pass count are recorded.
- Any failure becomes explicit follow-up work.

## Verification Plan

- Split into target-list construction, pytest execution, and result audit.
- Use P513 selected focused inventory as the source.
- Record all artifacts under `.complex-problems/L20260516-222011/tmp/`.

## Risks

- Unit/tool-output filters can accidentally overlap P518 or omit explicit dependency tests.
- Some tests may require a specific cwd; execution must preserve and document that contract.

## Assumptions

- P517 and P518 already cover session and task/saga/worker focused groups.
