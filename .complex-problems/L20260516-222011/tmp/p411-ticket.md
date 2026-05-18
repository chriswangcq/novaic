# Runtime cleanup final verification ticket

## Problem Definition

After runtime session-authority, generic Queue infrastructure, task/handler contracts, and worker counters are classified, a final runtime verification pass must prove no unclassified runtime compatibility residue remains.

## Proposed Solution

Rerun runtime-specific narrow and widened guards across queue_service and task_queue, map remaining hits to P407-P410 child classifications, and run a focused aggregate runtime test suite.

## Acceptance Criteria

- Final runtime guard output is saved.
- Every remaining runtime hit is classified through child evidence or final matrix.
- No attach/finalize/session-ended runtime path accepts missing/stale generation silently.
- Focused runtime aggregate tests pass.

## Verification Plan

- Run narrow live session-generation guard and widened runtime guard.
- Run focused runtime tests covering session authority, generic Queue infrastructure, task handlers/contracts, and workers.
- Record guard files and test counts.

## Risks

- Widened guard will remain noisy; success requires clear classification, not zero output.

## Assumptions

- Child problems P407-P410 are checked successful before this final verification.
