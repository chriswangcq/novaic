# Final finalize/session compatibility verification ticket

## Problem Definition

P492 must skeptically verify the full P482 finalize/session compatibility cleanup after inventory and targeted remediation. It needs to compare final guard output against the initial inventory, classify remaining hits, and prove focused finalize/session/attach/recovery tests pass together.

## Proposed Solution

Run the combined focused test suite spanning finalize ownership, attach generation, recovery/session-ended, legacy cleanup, and residue guards. Run final guard searches for known compatibility residue fields/paths. Save raw and classified artifacts under `.complex-problems/L20260516-222011/tmp/p492/`.

## Acceptance Criteria

- Final guard search artifact is saved.
- Remaining hits are classified with exact file references.
- No unclassified production residue remains.
- Focused finalize/session/attach/recovery tests pass together.

## Verification Plan

- Run focused pytest suite combining P489, P490, and P491 test sets.
- Run `rg` guard sweeps for legacy finalize/session terms, optional attach generation, recovery stack fallback fields, direct active-session mutation, and direct session task publication.
- Write final classification artifact and compare against P488 cleanup candidates.

## Risks

- Guard output will be noisy due to intentional tests and ledger artifacts; classification must focus on runtime source and relevant tests.
- This is focused verification, not full repository CI.

## Assumptions

- P489, P490, and P491 have been checked successful before P492 runs.
