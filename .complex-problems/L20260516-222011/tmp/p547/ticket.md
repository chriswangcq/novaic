# Reconcile low-density test classification

## Problem Definition

P547 must reconcile the two low-density child classifications under P543: the 2-4-hit bucket and the single-hit bucket. It must prove their combined counts cover the P543 remainder exactly and no risky low-density test residue remains.

## Proposed Solution

Compare P545 and P546 counts/classifications against the P543 remainder target of 64 hits across 38 files. Write a reconciliation artifact that records arithmetic, file ownership, and risk status.

## Acceptance Criteria

- P545 + P546 hit counts equal 64.
- P545 + P546 file counts equal 38.
- No low-density file is missing or double-counted.
- Any risky stale low-density test residue is absent or linked to a closed follow-up.

## Verification Plan

Use the filtered hit/count artifacts from P545 and P546 and compare them to the remainder counts derived during P543 split. Fail if counts mismatch or either child reports unresolved risk.

## Risks

- Arithmetic can be correct while file ownership overlaps; reconciliation should mention ownership source.

## Assumptions

- P545 and P546 are the only classification children under P543 before low-density reconciliation.
