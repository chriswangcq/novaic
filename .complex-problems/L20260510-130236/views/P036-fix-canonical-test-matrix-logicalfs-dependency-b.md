# P036: Fix Canonical Test Matrix LogicalFS Dependency Boundary

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P036
Body: problems/P000/children/P036/README.md
Ticket(s): T036

## Problem
The final root verification exposed that `scripts/run_all_tests.sh` ran `novaic-logicalfs` tests with `PYTHONPATH="."` only. After adding `logicalfs.blob_store`, the package explicitly depends on `novaic-common` for `common.http.clients`, so the canonical matrix failed even though package-local targeted tests passed with an explicit PYTHONPATH.

## Success Criteria
- `scripts/run_all_tests.sh` encodes the LogicalFS dependency boundary explicitly.
- The canonical test matrix passes end to end.
- The fix is recorded and checked before root problem closure.

## Subproblems
- none

## Results
- R036

## Latest Check
C037

## Bodies
- Problem: problems/P000/children/P036/README.md
- Ticket T036: problems/P000/children/P036/tickets/T036.md
- Result R036: problems/P000/children/P036/results/R036.md
- Check C037: problems/P000/children/P036/checks/C037.md

## Follow-ups
- none
