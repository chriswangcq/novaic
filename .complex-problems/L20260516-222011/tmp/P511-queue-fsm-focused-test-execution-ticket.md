# Queue FSM Focused Test Execution Ticket

## Problem Definition

P511 must execute the focused pytest suite selected by P510/P513 and record exact pass/fail counts and command output.

## Proposed Solution

Run pytest from `novaic-agent-runtime` using the selected focused test list generated at `.complex-problems/L20260516-222011/tmp/p513/selected-focused-test-files.txt`. Save the full log under the ledger tmp directory.

## Acceptance Criteria

- Focused pytest command exits successfully, or failure details are captured for follow-up.
- Exact command, selected file count, and pytest result count are recorded.
- Test scope covers dispatch, session state, outbox, finalize, recovery, saga compensation, and FSM decisions.

## Verification Plan

- Inspect the focused pytest log.
- Confirm selected test list count and pytest collected/passed counts.

## Risks

- Running a broad focused suite may reveal unrelated existing failures from dirty worktree state.
- Some selected files may be slower or integration-oriented.

## Assumptions

- The selected test list contains paths relative to repository root and should be converted relative to `novaic-agent-runtime` when running pytest from that package directory.
