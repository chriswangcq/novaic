# P029: Migrate Remaining Workspace Constructor Tests

Status: done
Parent: P028
Root: P000
Package: problems/P000/children/P019/children/P023/children/P028/children/P029
Body: problems/P000/children/P019/children/P023/children/P028/children/P029/README.md
Ticket(s): T028

## Problem
Tests outside `test_workspace.py` still create `Workspace(MemoryStore(), ...)` directly. This either fails after constructor cutover or encourages restoring a compatibility constructor. This belongs under P028 because test migration must enforce the new authority boundary.

## Success Criteria
- All live Workspace construction tests use explicit LogicalFS-backed helpers.
- No `Workspace(MemoryStore(), ...)` or `Workspace(store, ...)` live-constructor pattern remains outside object-store-only tests.
- Targeted Workspace/API/sandbox tests using direct Workspace construction pass.

## Subproblems
- none

## Results
- R025

## Latest Check
C025

## Bodies
- Problem: problems/P000/children/P019/children/P023/children/P028/children/P029/README.md
- Ticket T028: problems/P000/children/P019/children/P023/children/P028/children/P029/tickets/T028.md
- Result R025: problems/P000/children/P019/children/P023/children/P028/children/P029/results/R025.md
- Check C025: problems/P000/children/P019/children/P023/children/P028/children/P029/checks/C025.md

## Follow-ups
- none
