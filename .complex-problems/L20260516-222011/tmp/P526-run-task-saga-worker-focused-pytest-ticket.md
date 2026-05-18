# Run Task Saga Worker Focused Pytest Ticket

## Problem Definition

The P518 task/saga/worker target list exists and has been validated by P525, but it has not yet been executed. P526 must run pytest on that exact list and preserve exact evidence.

## Proposed Solution

Run pytest for `.complex-problems/L20260516-222011/tmp/p525/task-saga-worker-test-files.txt`, capture stdout/stderr to a P526 log, and record target count plus pytest exit code.

## Acceptance Criteria

- Pytest runs against exactly the P525 target list.
- The command, target count, exit code, and pytest summary are saved under `.complex-problems/L20260516-222011/tmp/p526/`.
- Empty-suite and partial-run false positives are rejected.
- Failures are recorded for follow-up rather than patched inside this ticket.

## Verification Plan

- Count target files before running pytest.
- Run pytest from the repository root so the P525 project-root paths are valid.
- Save the full pytest log and an execution counts file.
- Check the log for collected tests and final summary.

## Risks

- Running from the wrong directory could make the project-root target paths invalid.
- A green exit code with zero collected tests would be a false success.

## Assumptions

- P525 target list is the authoritative P526 input.
