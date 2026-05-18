# Queue FSM Static Residue Classification Ticket

## Problem Definition

P512 must run the final static residue scan designed by P514/P516 and classify every remaining hit for risky legacy/imperative queue/session/FSM paths.

## Proposed Solution

Use `.complex-problems/L20260516-222011/tmp/p514/guard-pattern.txt` as the scan pattern over the P514 scope. Split the work into raw scan execution and hit classification. Any risky production residue must become follow-up work instead of being hidden.

## Acceptance Criteria

- Static scan command and hit counts are recorded.
- Every remaining hit is classified as live/expected, test-only, documentation/comment, or follow-up-worthy.
- Production hits are separated from test hits.
- No unclassified risky legacy path remains.

## Verification Plan

- Run the P514 scan command and save raw output/counts.
- Build classification artifacts from the raw hits.
- Inspect production hits with enough context to decide whether each is expected or risky.
- If risky residue exists, create a follow-up problem.

## Risks

- The broad pattern will produce expected hits; success depends on classification quality, not zero hits.
- Tests intentionally containing legacy terms must not be mistaken for production residue.

## Assumptions

- P514/P516 guard pattern and scope are authoritative.
