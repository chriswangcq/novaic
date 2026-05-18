# Finalize producer stack contract audit ticket

## Problem Definition

P493 must find every producer of `wake_finalize` context and determine whether it supplies explicit `remaining_stack`. This is a read-only prerequisite for strict wake finalize behavior.

## Proposed Solution

Use `rg` to locate `wake_finalize`, `create_wake_finalize_saga`, `WAKE_FINALIZE_SAGA`, `force_finalize`, and `remaining_stack` producer paths. Inspect saga creation, compensation, and react action decision code. Save raw producer search output and a classification artifact.

## Acceptance Criteria

- Every production wake-finalize producer is listed.
- Each producer is classified as explicit stack provider, missing stack provider, or irrelevant/test fixture.
- Missing providers are identified for P494 or spawned if broader than P494.
- No source changes are made.

## Verification Plan

Read the matching producer code and compare it against the strict finalizer contract. Save artifacts under `.complex-problems/L20260516-222011/tmp/p493/`.

## Risks

- Some producer paths may use generic saga creation and only become visible through context keys.

## Assumptions

- P493 only audits producer contracts; P494 changes code.
