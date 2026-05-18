# Reconcile test residue classifications

## Problem Definition

P544 must reconcile all P535 test classification groups back to P531's test totals. It is the accounting step proving every test hit/file is classified exactly once and no risky test residue remains unhandled.

## Proposed Solution

Compare P541, P542, and P543 classification/count artifacts against P531 `test_hits=245` and `test_files=56`. Verify child risk status and write a durable reconciliation artifact.

## Acceptance Criteria

- Child classified hit counts sum to 245.
- Child classified file counts sum to 56.
- Every P531 test file is assigned to exactly one classification group.
- Risky stale test residue is absent or linked to closed follow-up.
- A durable reconciliation artifact is written for P535.

## Verification Plan

Use P541/P542/P543 results and file-list set arithmetic to verify counts, ownership, and risk closure. Fail if counts mismatch or any child has unresolved risk.

## Risks

- Correct arithmetic can still hide overlap; set reconciliation must check overlap/missing/extra files.

## Assumptions

- P541, P542, and P543 are the complete split children that classify all P535 test hits.
