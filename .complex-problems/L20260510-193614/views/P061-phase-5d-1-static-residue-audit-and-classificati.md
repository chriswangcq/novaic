# P061: Phase 5D.1 Static Residue Audit And Classification

Status: done
Parent: P048
Root: P000
Package: problems/P000/children/P006/children/P048/children/P061
Body: problems/P000/children/P006/children/P048/children/P061/README.md
Ticket(s): T061

## Problem
Run the broad static residue audit for old local-authority and compatibility patterns across current docs, architecture docs, Cortex source, and agent-runtime integration surfaces. The output must classify every remaining hit instead of treating grep noise as success.

This belongs under P048 because static residue classification is the first proof that cleanup did not leave current stale guidance behind.

## Success Criteria
- Run broad `rg` audits for transition-log authority, active-stack file walking, temp backing-path authority, process-local fallback, in-process locks, and obsolete compatibility phrases.
- Classify all remaining matches as current defect, historical, negative guard, test-only, migration internals, or low-level projection internals.
- If a current defect is found, either fix it inside the ticket when small and verify, or create a follow-up problem.
- Record exact commands and classification evidence.

## Subproblems
- none

## Results
- R058

## Latest Check
C062

## Bodies
- Problem: problems/P000/children/P006/children/P048/children/P061/README.md
- Ticket T061: problems/P000/children/P006/children/P048/children/P061/tickets/T061.md
- Result R058: problems/P000/children/P006/children/P048/children/P061/results/R058.md
- Check C062: problems/P000/children/P006/children/P048/children/P061/checks/C062.md

## Follow-ups
- none
