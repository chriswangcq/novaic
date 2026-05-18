# Classify test residue hits by purpose groups

## Problem Definition

P535 must classify 245 static-residue hits across 56 test files. These hits may be expected regression coverage for old failures, FSM boundary tests, cleanup guardrails, or stale misleading tests that should be removed or rewritten.

## Proposed Solution

Split the classification by test purpose rather than trying to judge all 56 files in one pass. Create child problems for lifecycle/recovery tests, cutover/guardrail tests, miscellaneous low-count boundary tests, and final reconciliation. Each child will classify its file group with counts/rationale and surface follow-up-worthy stale tests.

## Acceptance Criteria

- All 245 P531 test hits are assigned to exactly one child classification group.
- Every test file with hits gets a purpose/category rationale.
- Stale or misleading tests become follow-up problems.
- Child counts reconcile back to P531 test totals.

## Verification Plan

Use P531 `static-residue-tests.txt` as the source of truth. Each child writes a filtered hit file, count summary, and classification artifact. The reconciliation child verifies child hit/file totals equal P531's 245 test hits and 56 test files.

## Risks

- Tests intentionally mention old vocabulary to prevent regressions; deleting those blindly would weaken guardrails.
- Some PR-named tests mix lifecycle and cutover semantics, so grouping needs explicit file ownership to prevent double counting.
- Large one-pass classification would hide stale tests, so split is preferred.

## Assumptions

- Test residue classification should preserve useful regression coverage while removing only misleading or dead tests.
