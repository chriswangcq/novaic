# P023: Cut Cortex Workspace Runtime To LogicalFS Authority

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P019/children/P023
Body: problems/P000/children/P019/children/P023/README.md
Ticket(s): T023

## Problem
Cortex must become a semantic client of LogicalFS instead of owning the live file persistence adapter. Workspace, runtime, API, and registry need to use the new LogicalFS authority in the active path. This belongs under T019 because defining a new authority is insufficient unless the live agent runtime is cut over to it.

## Success Criteria
- `Workspace` accepts or constructs only a LogicalFS authority/port for live file operations, not `CortexStore` or Blob persistence.
- Runtime/API/registry active construction paths pass explicit semantic owner/layout inputs into LogicalFS.
- Shell/sandbox RO/RW behavior still works through the cutover path.
- Existing tests are updated to use explicit LogicalFS test authorities or helpers rather than active direct store construction.
- Residue scans show no active `ws._store` or direct store access in Workspace/runtime/API.

## Subproblems
- P025: Add Cortex Workspace LogicalFS Factory And Test Authority Helper
- P026: Refactor Workspace To Depend On LogicalFS Authority
- P027: Refactor Runtime And Registry Wiring To LogicalFS Authority
- P028: Migrate Cortex Tests And Prove Shell Cutover

## Results
- R029

## Latest Check
C029

## Bodies
- Problem: problems/P000/children/P019/children/P023/README.md
- Ticket T023: problems/P000/children/P019/children/P023/tickets/T023.md
- Result R029: problems/P000/children/P019/children/P023/results/R029.md
- Check C029: problems/P000/children/P019/children/P023/checks/C029.md

## Follow-ups
- none
