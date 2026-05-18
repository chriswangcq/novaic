# Build Task Saga Worker Test Subset Ticket

## Problem Definition

P518 needs a focused pytest target list for task/saga/worker/FSM/control-plane verification. The list must be derived from the P513 selected focused inventory and must not include non-test paths or silently miss obvious coverage areas.

## Proposed Solution

Filter the P513 selected focused test file list using explicit task/saga/worker/FSM/control-plane terms. Save the selected target list, count artifacts, filter terms, and a coverage note that maps selected files back to P518's stated scope.

## Acceptance Criteria

- The target list exists under the ledger tmp directory.
- Every selected path exists under `novaic-agent-runtime` and is a `test_*.py` file.
- The filter terms and selection count are recorded.
- Coverage mapping explicitly addresses generic FSM substrate, task queue FSM, saga FSM, worker lease/generic worker, queue control plane, busy behavior, and recovery behavior.

## Verification Plan

- Use shell checks (`wc`, `sed`, `while read test -f`, basename pattern checks) to validate the list.
- Save all evidence artifacts under `.complex-problems/L20260516-222011/tmp/p525/`.
- Do not run pytest in this ticket; execution belongs to P526.

## Risks

- Too-broad filters could include unrelated tests.
- Too-narrow filters could omit relevant worker/FSM coverage.

## Assumptions

- `.complex-problems/L20260516-222011/tmp/p513/selected-focused-test-files.txt` is the authoritative selected focused inventory.
