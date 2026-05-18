# Rerun Session Outbox Finalize Subset Ticket

## Problem Definition

The full P517 session/outbox/finalize subset must be rerun after targeted repairs to prove the subset is green.

## Proposed Solution

Run pytest from `novaic-agent-runtime` using `.complex-problems/L20260516-222011/tmp/p517/session-outbox-finalize-test-files.txt` and save a fresh rerun log.

## Acceptance Criteria

- Pytest exits successfully.
- Exact command, subset count, and pass count are recorded.
- Rerun log is saved under P524 artifacts.

## Verification Plan

- Inspect the rerun log.
- Confirm pytest summary is passing.

## Risks

- Additional failures may surface after the first three repairs.

## Assumptions

- The subset file contains paths relative to `novaic-agent-runtime`.
