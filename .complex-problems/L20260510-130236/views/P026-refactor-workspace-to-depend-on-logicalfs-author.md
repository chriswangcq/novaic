# P026: Refactor Workspace To Depend On LogicalFS Authority

Status: done
Parent: P023
Root: P000
Package: problems/P000/children/P019/children/P023/children/P026
Body: problems/P000/children/P019/children/P023/children/P026/README.md
Ticket(s): T025

## Problem
`Workspace.__init__` still accepts a direct `CortexStore` and constructs `CortexLogicalFileAuthority`. This keeps live file authority inside Cortex. This belongs under P023 because Workspace is the central active dependency boundary.

## Success Criteria
- `Workspace.__init__` accepts a LogicalFS authority/port, not `CortexStore`.
- `workspace.py` no longer imports `CortexStore`, `CortexLogicalFileAuthority`, or `logical_to_store_key`.
- Directory listing maps LogicalFS directory entries to Cortex `FileEntry` without leaking store keys.
- Workspace initialization writes default layout through the authority explicitly.
- Targeted Workspace tests pass through the new constructor/helper.

## Subproblems
- none

## Results
- R023

## Latest Check
C023

## Bodies
- Problem: problems/P000/children/P019/children/P023/children/P026/README.md
- Ticket T025: problems/P000/children/P019/children/P023/children/P026/tickets/T025.md
- Result R023: problems/P000/children/P019/children/P023/children/P026/results/R023.md
- Check C023: problems/P000/children/P019/children/P023/children/P026/checks/C023.md

## Follow-ups
- none
