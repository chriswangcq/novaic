# Audit Static Residue Classification

## Problem Definition

P512 has a static residue scan plus production/test classification children. Before closing the static residue branch, audit the current repository against those artifacts and verify that the classification is complete, the risky residue found during classification has been removed, and any remaining residue is either intentionally classified or captured as a follow-up.

## Proposed Solution

Run a fresh static residue scan using the same search pattern as the P531 baseline, compare current counts against the recorded classification totals, inspect the risky saga optional-step cleanup area, and reconcile the P534/P535/P536/P532 result/check artifacts. Record an audit result with exact evidence file paths and residual risk.

## Acceptance Criteria

- Fresh scan output is stored under the P533 workspace package.
- The audit cites the P531 raw baseline and the production/test classification artifacts.
- Production and test hit totals are reconciled or any discrepancy is explained.
- The previously detected risky `SagaStep.optional` / `optional=True` API residue is proven absent or escalated as a follow-up.
- Remaining residual risk is explicit.

## Verification Plan

Use `rg` for the static residue pattern, targeted `rg` checks for optional saga APIs, and ledger artifact inspection for P531/P534/P535/P536/P532. If the scan or reconciliation reveals unclassified risky residue, create a follow-up problem instead of marking success.

## Risks

- Static grep can over-count benign documentation or test names.
- A stale residue pattern can miss a newly introduced risky path with different terminology.
- Counts may shift after legitimate cleanup; the audit must distinguish expected delta from missing classification.

## Assumptions

- P531/P534/P535/P536/P532 artifacts are the authoritative prior classification artifacts for this ledger branch.
- Current repository state includes the P540 saga optional-step cleanup.
- P533 is an audit gate, so it should not make unrelated code changes unless the audit finds a direct closure gap.
