# P031: Full Cutover Verification And Residue Scan

Status: done
Parent: P028
Root: P000
Package: problems/P000/children/P019/children/P023/children/P028/children/P031
Body: problems/P000/children/P019/children/P023/children/P028/children/P031/README.md
Ticket(s): T030

## Problem
After migrating tests, the suite and scans must prove there is no unconnected new code, hidden compatibility branch, or stale active test path. This belongs under P028 because successful test migration must be verified as a whole.

## Success Criteria
- Full Cortex test suite passes.
- LogicalFS and sandbox-service targeted suites still pass.
- Residue scans show no old direct live constructor patterns in Cortex source/tests.
- Shell/sandbox RO/RW wiring tests pass.
- Any remaining old store modules are classified for P024 cleanup rather than silently accepted.

## Subproblems
- none

## Results
- R027

## Latest Check
C027

## Bodies
- Problem: problems/P000/children/P019/children/P023/children/P028/children/P031/README.md
- Ticket T030: problems/P000/children/P019/children/P023/children/P028/children/P031/tickets/T030.md
- Result R027: problems/P000/children/P019/children/P023/children/P028/children/P031/results/R027.md
- Check C027: problems/P000/children/P019/children/P023/children/P028/children/P031/checks/C027.md

## Follow-ups
- none
