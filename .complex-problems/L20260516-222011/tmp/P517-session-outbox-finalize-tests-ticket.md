# Session Outbox Finalize Focused Tests Ticket

## Problem Definition

Run the focused tests that cover session dispatch/state, outbox, attach/wake creation, finalize, recovery, and remaining-stack ownership.

## Proposed Solution

Build a subset from the selected focused test list using session/outbox/finalize/recovery/dispatch/wake/turn-finalizer filename terms, run pytest from `novaic-agent-runtime`, and save the full log.

## Acceptance Criteria

- Subset file count is recorded.
- Pytest exits successfully or failure details are recorded.
- Log path and pytest counts are captured.

## Verification Plan

- Inspect subset file list and pytest log.
- Confirm no selected path falls outside `test_*.py`.

## Risks

- Filename-based grouping may omit a relevant session test with generic naming, but P519 covers shared boundary tests and P512 covers static residue.

## Assumptions

- Running from `novaic-agent-runtime` requires stripping the `novaic-agent-runtime/` prefix from selected paths.
