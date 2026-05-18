# Reconcile test residue classifications

## Problem

Reconcile all child test-residue classifications back to P531's test totals. This is the accounting child that proves no test hit or test file was lost between the purpose groups.

## Success Criteria

- Child classified hit counts sum to P531 `test_hits=245`.
- Child classified file counts sum to P531 `test_files=56`.
- Every P531 test file is assigned to exactly one classification group.
- Any risky stale test residue is absent or linked to a closed follow-up.
- A durable reconciliation artifact is written for P535.
