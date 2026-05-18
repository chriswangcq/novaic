# Final Focused Runtime Verification

## Problem Definition

After P504 classification and P505 cleanup, P506 must prove the imperative dispatch cleanup is still safe at runtime and that final guard outputs no longer contain unclassified production residue.

## Proposed Solution

Rerun the production guard sweep after cleanup, save a final classification delta, run the focused runtime/session/FSM/outbox test suite, and produce an evidence bundle that maps P483 acceptance criteria to concrete artifacts.

## Acceptance Criteria

- Final production guard sweep is saved after P505 cleanup.
- Final guard classification confirms no unclassified production residue remains.
- Focused runtime/session/FSM/outbox tests pass from the correct repo root.
- P483 acceptance criteria are mapped to saved evidence.
- Any remaining ambiguity is converted into a follow-up instead of waived.

## Verification Plan

Run the same production guard categories as P504, compare against P504/P505 artifacts, run the focused test suite, save logs and final classification, then record the result with explicit residual risk.

## Risks

- Existing dirty files from prior tickets can make raw `git diff` noisy; final evidence must use focused artifacts and test logs.
- Guard terms can overmatch required boundaries, so production hits must be classified rather than counted naively.

## Assumptions

- P504 and P505 are closed successfully.
- Final broad parent success will be checked after P506 closes.
