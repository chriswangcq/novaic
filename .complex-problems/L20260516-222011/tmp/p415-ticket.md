# Task contract and handler final verification ticket

## Problem Definition

After React contracts, finalize/session handlers, and Cortex handler/bridge classification, the task/handler layer needs a final guard and test pass proving no unclassified task-level compatibility residue remains.

## Proposed Solution

Rerun targeted guards across the full task/handler file set, summarize all remaining hits using child results `P412`-`P414`, and run focused runtime/Cortex tests.

## Acceptance Criteria

- Full task/handler guard output is saved.
- Every remaining hit is classified by child evidence or final matrix.
- No task/handler path defaults live session generation.
- Focused runtime/Cortex tests pass.

## Verification Plan

- Run `rg` over React contracts, finalize sagas, session/Cortex handlers, and Cortex bridge.
- Run focused runtime contract/handler/finalize tests.
- Run focused Cortex archive/context tests if scope-end bridge is included.

## Risks

- A final guard can be overly broad; false positives must be classified, not ignored.

## Assumptions

- Child results `P412`, `P413`, and `P414` are already checked successful.
