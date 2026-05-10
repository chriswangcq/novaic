# Verify Finalize Wiring And Remove Residue

## Problem Definition

P027 and P028 implemented helper plus live archive wiring. P029 must verify the whole finalize feature as the active path, not just code beside the path. It must cover empty stack, non-empty stack, retry/idempotency, projection clearing, hard-coded residue, and full regression tests.

## Proposed Solution

Perform a strict verification and cleanup pass:

- Add any missing empty-stack live archive test.
- Confirm non-empty child-stack archive test asserts operational finalize payload and projection clearing.
- Confirm retry/idempotency test proves no duplicate conflicting events.
- Run static searches for hard-coded live `remaining_stack=[]`, unused helper paths, and old archive residue.
- Run targeted tests and full Cortex tests.
- If a gap is found, fix it in this ticket and rerun checks.

## Acceptance Criteria

- Empty-stack live archive/finalize test exists and passes.
- Non-empty live archive/finalize test exists and passes.
- Retry/idempotency test exists and passes.
- Projection clearing is asserted.
- Static residue search shows no live API archive authority hard-coding `remaining_stack=[]`.
- Targeted and full Cortex tests pass.

## Verification Plan

- Search relevant live code and tests with `rg`.
- Run targeted finalize/archive/context/active-stack tests.
- Run full `novaic-cortex/tests`.

## Risks

- If empty-stack root archive is not currently covered, the ticket must add it rather than accepting helper-only coverage.
- Static search may find valid test fixtures; distinguish live code from tests.

## Assumptions

- P029 is allowed to add or adjust tests and small code cleanup discovered by the residue pass.
