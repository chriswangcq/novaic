# P006: Phase 5: Legacy cleanup, reset behavior, and full verification

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P006
Body: problems/P000/children/P006/README.md
Ticket(s): T057

## Problem
Remove misleading legacy DFS-source residue, implement old-data reset/no-compat behavior, and run comprehensive checks. The codebase should leave one clear current path for Cortex context source semantics.

## Success Criteria
- Legacy source-of-truth paths and stale docs/comments are deleted or rewritten as projection/debug only.
- Old data reset behavior is explicit and tested.
- Full relevant test suites pass.
- Diff review confirms no permanent double-write/double-read ambiguity.
- Residual risks are documented and non-blocking.

## Subproblems
- P058: Legacy DFS deletion inventory
- P059: Old data reset and no-compat behavior
- P060: Source-of-truth language and artifact cleanup
- P061: Phase 5 final verification and diff review

## Results
- R061

## Latest Check
C065

## Bodies
- Problem: problems/P000/children/P006/README.md
- Ticket T057: problems/P000/children/P006/tickets/T057.md
- Result R061: problems/P000/children/P006/results/R061.md
- Check C065: problems/P000/children/P006/checks/C065.md

## Follow-ups
- none
