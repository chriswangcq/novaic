# P004: Verify CLI blob contract and clean residual old behavior

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T006

## Problem
After CLI repairs, tests and residue scans must prove the active shell CLI paths follow the blob artifact contract and do not silently keep raw base64/media stdout branches alive.

## Success Criteria
- Focused tests cover repaired CLI output contract.
- Existing projection/runtime tests still pass.
- Repository scans find no live raw screenshot/base64 stdout contract in shell CLI paths.
- Any residual compatibility branch is either removed or explicitly justified as test-only/non-live.

## Subproblems
- P007: Clean stale CLI artifact Blob namespace fixtures
- P008: Final CLI Blob contract verification

## Results
- R007

## Latest Check
C007

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T006: problems/P000/children/P004/tickets/T006.md
- Result R007: problems/P000/children/P004/results/R007.md
- Check C007: problems/P000/children/P004/checks/C007.md

## Follow-ups
- none
