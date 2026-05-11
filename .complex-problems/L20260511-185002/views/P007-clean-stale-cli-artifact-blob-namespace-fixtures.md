# P007: Clean stale CLI artifact Blob namespace fixtures

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P007
Body: problems/P000/children/P004/children/P007/README.md
Ticket(s): T007

## Problem
Some tests/examples still use pre-contract artifact namespaces such as `device-screenshot`. These residues can mislead future CLI implementations even if live code is fixed.

## Success Criteria
- Runtime-generated artifact fixtures use `blob://runtime-artifact/...`.
- No `device-screenshot` namespace remains in CLI/tool-output contract tests.
- Changes are limited to contract-relevant fixtures and do not rewrite unrelated storage tests.
- Relevant projection and tool-output tests pass.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P004/children/P007/README.md
- Ticket T007: problems/P000/children/P004/children/P007/tickets/T007.md
- Result R005: problems/P000/children/P004/children/P007/results/R005.md
- Check C005: problems/P000/children/P004/children/P007/checks/C005.md

## Follow-ups
- none
