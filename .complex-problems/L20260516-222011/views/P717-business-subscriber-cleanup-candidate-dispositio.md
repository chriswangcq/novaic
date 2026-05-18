# P717: Business/subscriber cleanup candidate disposition

Status: done
Parent: P716
Root: P000
Source Ticket: T708 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P717
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P717/README.md
Ticket(s): T709

## Problem
Review the cleanup candidates from P715 and classify each as active stale claim, intentional historical/current comparison, test-only fixture, already-clean code path, or follow-up-worthy broad cleanup. This belongs under P716 because remediation should not patch blindly without first separating active residue from intentional references.

## Success Criteria
- P715 cleanup candidates are enumerated and classified.
- `docs/entangled-architecture.md` Gateway/Business CRUD wording receives an explicit disposition.
- Launch/docs scan hits that mention Business/subscriber plus Queue/Runtime/Cortex/Gateway/Device/Entangled are sampled enough to justify the remediation scope.
- Any candidate that is too broad for safe direct patching is named as a follow-up candidate rather than ignored.

## Subproblems
- none

## Results
- R701

## Latest Check
C745

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P717/README.md
- Ticket T709: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P717/tickets/T709.md
- Result R701: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P717/results/R701.md
- Check C745: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P717/checks/C745.md

## Follow-ups
- none
