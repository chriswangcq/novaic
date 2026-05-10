# P028: Migrate Cortex Tests And Prove Shell Cutover

Status: done
Parent: P023
Root: P000
Package: problems/P000/children/P019/children/P023/children/P028
Body: problems/P000/children/P019/children/P023/children/P028/README.md
Ticket(s): T027

## Problem
Many tests still instantiate `Workspace(MemoryStore(), ...)` or `Cortex(MemoryStore(), ...)`. Even after code refactor, tests can preserve compatibility paths or miss active shell behavior. This belongs under P023 because successful cutover must be verified through the same behavior surfaces the runtime uses.

## Success Criteria
- Cortex tests are migrated to explicit LogicalFS-backed helpers.
- Targeted tests for Workspace, runtime, API sandbox wiring, and shell RW patch persistence pass.
- Full Cortex test suite passes.
- Residue scans show no direct `Workspace(MemoryStore`, `Cortex(MemoryStore`, `Cortex(store`, or old authority imports in tests except clearly isolated object-store unit tests.

## Subproblems
- P029: Migrate Remaining Workspace Constructor Tests
- P030: Migrate Direct Cortex Constructor Tests
- P031: Full Cutover Verification And Residue Scan

## Results
- R028

## Latest Check
C028

## Bodies
- Problem: problems/P000/children/P019/children/P023/children/P028/README.md
- Ticket T027: problems/P000/children/P019/children/P023/children/P028/tickets/T027.md
- Result R028: problems/P000/children/P019/children/P023/children/P028/results/R028.md
- Check C028: problems/P000/children/P019/children/P023/children/P028/checks/C028.md

## Follow-ups
- none
