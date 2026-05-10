# P006: Process Cache Config And Documentation Residue Cleanup

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P006
Body: problems/P000/children/P006/README.md
Ticket(s): T006

## Problem
Cortex still has process-local registry caches, startup config, lock backend globals, and some stale comments. These are mostly not durable authority, but they can confuse future maintainers and tests.

## Success Criteria
- Classify which process-local state is allowed cache/config.
- Define explicit dependency boundaries for caches, clocks, ids, env, and service clients.
- Identify documentation/code residue to clean so future agents do not infer wrong architecture.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P006/README.md
- Ticket T006: problems/P000/children/P006/tickets/T006.md
- Result R005: problems/P000/children/P006/results/R005.md
- Check C005: problems/P000/children/P006/checks/C005.md

## Follow-ups
- none
