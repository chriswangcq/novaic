# P001: Audit Cortex LogicalFS and Sandbox adapter cutover

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Find any remaining live code paths where Cortex/Sandbox/LogicalFS still bypass the intended lightweight LogicalFS adapter model, especially broad `/ro` materialization, direct Blob/Workspace filesystem reads inside shell paths, old fallback mounts, or local execution fallback.

## Success Criteria
- Search and inspect LogicalFS, Sandbox, sandboxd, Workspace, and shell execution paths.
- Confirm whether any broad recursive materialization remains on shell/live execution paths.
- Separate runtime code findings from docs/tests.
- Record exact file/function evidence and any needed follow-up.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
